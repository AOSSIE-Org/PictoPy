from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.config.settings import CONFIDENCE_PERCENT
from app.database.faces import db_get_all_video_face_embeddings, get_all_face_embeddings
from app.database.videos import db_get_videos_by_ids
from app.models.FaceDetector import FaceDetector
from app.schemas.videos import VideoData
from app.utils.FaceNet import FaceNet_util_cosine_similarity
from app.utils.videos import video_util_to_video_data


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
        matches = []

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

        images = get_all_face_embeddings()
        video_faces = db_get_all_video_face_embeddings()
        if not images and not video_faces:
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

        # Several keyframe faces can belong to one video, so rank each video by
        # its best-matching face rather than listing it once per keyframe.
        best_by_video: Dict[str, float] = {}
        for face in video_faces:
            similarity = FaceNet_util_cosine_similarity(
                new_embedding, face["embeddings"]
            )
            if similarity >= CONFIDENCE_PERCENT:
                video_id = face["video_id"]
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
