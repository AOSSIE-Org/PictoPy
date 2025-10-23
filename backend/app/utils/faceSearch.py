import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.config.settings import CONFIDENCE_PERCENT, DEFAULT_FACENET_MODEL
from app.database.faces import get_all_face_embeddings
from app.models.FaceDetector import FaceDetector
from app.models.FaceNet import FaceNet
from app.utils.FaceNet import FaceNet_util_cosine_similarity


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class ImageData(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: Dict[str, Any]
    isTagged: bool
    tags: Optional[List[str]] = None
    bboxes: BoundingBox


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]


def perform_face_search(image_path: str) -> GetAllImagesResponse:
    """
    Performs face detection, embedding generation, and similarity search.

    Args:
        image_path (str): Path to the image file to process.

    Returns:
        GetAllImagesResponse: Search result containing matched images.
    """
    fd = FaceDetector()
    fn = FaceNet(DEFAULT_FACENET_MODEL)

    try:
        matches = []
        image_id = str(uuid.uuid4())

        try:
            result = fd.detect_faces(image_id, image_path, forSearch=True)
        except Exception as e:
            return GetAllImagesResponse(
                success=False,
                message=f"Failed to process image: {str(e)}",
                data=[],
            )
        if not result or result["num_faces"] == 0:
            return GetAllImagesResponse(
                success=True,
                message="No faces detected in the image.",
                data=[],
            )

        process_face = result["processed_faces"][0]
        new_embedding = fn.get_embedding(process_face)

        images = get_all_face_embeddings()
        if not images:
            return GetAllImagesResponse(
                success=True,
                message="No face embeddings available for comparison.",
                data=[],
            )

        for image in images:
            similarity = FaceNet_util_cosine_similarity(
                new_embedding, image["embeddings"]
            )
            if similarity >= CONFIDENCE_PERCENT:
                matches.append(
                    ImageData(
                        id=image["id"],
                        path=image["path"],
                        folder_id=image["folder_id"],
                        thumbnailPath=image["thumbnailPath"],
                        metadata=image["metadata"],
                        isTagged=image["isTagged"],
                        tags=image["tags"],
                        bboxes=image["bbox"],
                    )
                )

        return GetAllImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(matches)} matching images.",
            data=matches,
        )

    finally:
        if "fd" in locals() and fd is not None:
            fd.close()
        if "fn" in locals() and fn is not None:
            fn.close()
