from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, ValidationError
from app.config.settings import CONFIDENCE_PERCENT
from app.database.faces import (
    db_get_all_image_face_embeddings,
    db_get_all_video_face_embeddings,
)
from app.database.images import db_get_images_by_ids
from app.database.videos import db_get_videos_by_ids
from app.logging.setup_logging import get_logger
from app.models.FaceDetector import FaceDetector
from app.schemas.videos import VideoData
from app.utils.FaceNet import FaceNet_util_cosine_similarity
from app.utils.images import image_util_parse_metadata
from app.utils.videos import video_util_to_video_data

logger = get_logger(__name__)


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
    # The matching face's box, absent on faces stored before one was recorded.
    bboxes: Optional[BoundingBox] = None


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]
    # Videos the same face was found in, best match first.
    videos: List[VideoData] = []


def perform_face_search(image_path: str) -> GetAllImagesResponse:
    """
    Performs face detection, embedding generation, and similarity search.

    Args:
        image_path (str): Path to the image file to process.

    Returns:
        GetAllImagesResponse: Search result containing matched images.
    """
    fd = FaceDetector()

    try:
        try:
            result = fd.detect_faces(image_path)
        except Exception as e:
            return GetAllImagesResponse(
                success=False,
                message=f"Failed to process image: {str(e)}",
                data=[],
            )
        if not result or not result["embeddings"]:
            return GetAllImagesResponse(
                success=True,
                message="No faces detected in the image.",
                data=[],
            )

        # The detector already ran FaceNet on this crop; no second model needed.
        new_embedding = result["embeddings"][0]

        image_faces = db_get_all_image_face_embeddings()
        video_faces = db_get_all_video_face_embeddings()
        if not image_faces and not video_faces:
            return GetAllImagesResponse(
                success=True,
                message="No face embeddings available for comparison.",
                data=[],
            )

        # A group photo holds several people, so rank each image by its
        # best-matching face and frame that one, rather than whichever face the
        # database happened to return first.
        best_by_image: Dict[str, Tuple[float, Optional[Dict[str, Any]]]] = {}
        for face in image_faces:
            similarity = FaceNet_util_cosine_similarity(
                new_embedding, face["embeddings"]
            )
            if similarity >= CONFIDENCE_PERCENT:
                image_id = face["image_id"]
                previous = best_by_image.get(image_id)
                if previous is None or similarity > previous[0]:
                    best_by_image[image_id] = (similarity, face["bbox"])

        matched_ids = sorted(
            best_by_image, key=lambda i: best_by_image[i][0], reverse=True
        )
        # Loaded by id so paths, metadata and tags are only read for the images
        # that actually matched. Row by row: one unusable record must not fail
        # the search and hide every other match.
        matches: List[ImageData] = []
        for image in db_get_images_by_ids(matched_ids):
            _, bbox = best_by_image[image["id"]]
            try:
                matches.append(
                    ImageData(
                        id=image["id"],
                        path=image["path"],
                        folder_id=image["folder_id"],
                        thumbnailPath=image["thumbnailPath"],
                        metadata=image_util_parse_metadata(image["metadata"]),
                        isTagged=image["isTagged"],
                        tags=image["tags"],
                        bboxes=bbox,
                    )
                )
            except ValidationError as e:
                logger.warning(
                    f"Skipping image {image.get('id')} with invalid metadata: {e}"
                )

        # Several keyframe faces can belong to one video, so rank each video by
        # its best-matching face rather than listing it once per keyframe.
        best_by_video: Dict[str, float] = {}
        for video_face in video_faces:
            similarity = FaceNet_util_cosine_similarity(
                new_embedding, video_face["embeddings"]
            )
            if similarity >= CONFIDENCE_PERCENT:
                video_id = video_face["video_id"]
                if similarity > best_by_video.get(video_id, 0.0):
                    best_by_video[video_id] = similarity

        ranked = sorted(best_by_video, key=lambda v: best_by_video[v], reverse=True)
        videos = video_util_to_video_data(db_get_videos_by_ids(ranked))

        return GetAllImagesResponse(
            success=True,
            message=(
                f"Successfully retrieved {len(matches)} matching images "
                f"and {len(videos)} matching video(s)."
            ),
            data=matches,
            videos=videos,
        )

    finally:
        if "fd" in locals() and fd is not None:
            fd.close()
