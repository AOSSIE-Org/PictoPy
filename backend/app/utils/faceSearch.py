import hashlib
import threading
import time
from collections import OrderedDict
from typing import Optional, List, Dict, Any, NamedTuple, Sequence, Tuple
import numpy as np
from pydantic import BaseModel, ValidationError
from scipy.optimize import linear_sum_assignment
from app.config.settings import CONFIDENCE_PERCENT, FACE_SEARCH_MAX_SELECTED_FACES
from app.database.faces import (
    db_get_all_image_face_embeddings,
    db_get_all_video_face_embeddings,
)
from app.database.images import db_get_images_by_ids
from app.database.videos import db_get_videos_by_ids
from app.models.FaceDetector import FaceDetectionResult, FaceDetector
from app.schemas.videos import VideoData
from app.logging.setup_logging import get_logger
from app.utils.FaceNet import FaceNet_util_cosine_similarity
from app.utils.images import image_util_parse_metadata
from app.utils.videos import video_util_to_video_data

logger = get_logger(__name__)

# Picking faces takes two requests on one photo, detect-faces and then
# face-search. Keeping the detection between them skips the second model run and
# guarantees both see the same faces in the same order.
_DETECTION_CACHE_SIZE = 8
_DETECTION_CACHE_TTL_SECONDS = 600
_detection_cache: "OrderedDict[str, Tuple[float, FaceDetectionResult]]" = OrderedDict()
_detection_cache_lock = threading.Lock()


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
    # Absent for faces stored without a box.
    bboxes: Optional[BoundingBox] = None
    # How many of the selected faces this photo matched.
    match_count: Optional[int] = None


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]
    # Videos the same face was found in, best match first.
    videos: List[VideoData] = []


class DetectedFace(BaseModel):
    index: int
    bbox: BoundingBox
    confidence: float


class DetectFacesData(BaseModel):
    image_width: int
    image_height: int
    faces: List[DetectedFace]
    faces_skipped: int


class DetectFacesResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DetectFacesData] = None


class InvalidFaceSelection(ValueError):
    """The requested face indices do not exist in the query photo."""


def clear_detection_cache() -> None:
    with _detection_cache_lock:
        _detection_cache.clear()


def _image_digest(image_path: str) -> Optional[str]:
    """Identifies a photo by its content, so a re-saved file is never mixed up."""
    try:
        with open(image_path, "rb") as image_file:
            return hashlib.sha256(image_file.read()).hexdigest()
    except OSError:
        return None


def _detect_faces_cached(image_path: str) -> Optional[FaceDetectionResult]:
    """
    Detect the faces of a photo, reusing a recent detection of the same bytes.

    Raises whatever the detector raises; failures are never cached.
    """
    digest = _image_digest(image_path)
    now = time.monotonic()
    if digest is not None:
        with _detection_cache_lock:
            cached = _detection_cache.get(digest)
            if cached and now - cached[0] < _DETECTION_CACHE_TTL_SECONDS:
                _detection_cache.move_to_end(digest)
                return cached[1]

    fd = FaceDetector()
    try:
        result = fd.detect_faces(image_path)
    finally:
        fd.close()

    if digest is not None and result:
        with _detection_cache_lock:
            _detection_cache[digest] = (now, result)
            _detection_cache.move_to_end(digest)
            while len(_detection_cache) > _DETECTION_CACHE_SIZE:
                _detection_cache.popitem(last=False)
    return result


class _GroupMatch(NamedTuple):
    score: float
    bbox: Optional[Dict[str, Any]]
    match_count: int


# Far below any similarity, so no full assignment can include a pair that did
# not reach CONFIDENCE_PERCENT.
_NO_MATCH = -1000.0


def _score_groups(
    queries: Sequence[Any],
    faces: List[Dict[str, Any]],
    group_key: str,
    match_mode: str,
) -> Dict[str, _GroupMatch]:
    """
    Score every image (or video) that holds a stored face close to the queries.

    match_any keeps a group when any query reaches CONFIDENCE_PERCENT and scores
    it by its best face. match_all keeps it only when every query can be matched
    to a different stored face, so one face never answers two queries, and scores
    it by the mean similarity of the best such assignment.
    """
    faces_by_group: Dict[str, List[Dict[str, Any]]] = {}
    for face in faces:
        faces_by_group.setdefault(face[group_key], []).append(face)

    scored: Dict[str, _GroupMatch] = {}
    for group_id, group_faces in faces_by_group.items():
        pairs: List[Tuple[float, int, int]] = []
        for face_pos, face in enumerate(group_faces):
            for query_pos, query in enumerate(queries):
                similarity = FaceNet_util_cosine_similarity(query, face["embeddings"])
                if similarity >= CONFIDENCE_PERCENT:
                    pairs.append((similarity, query_pos, face_pos))
        if not pairs:
            continue
        pairs.sort(reverse=True)

        if match_mode == "match_any":
            best_similarity, _, best_face = pairs[0]
            scored[group_id] = _GroupMatch(
                best_similarity,
                group_faces[best_face].get("bbox"),
                len({query_pos for _, query_pos, _ in pairs}),
            )
            continue

        # Every query needs its own stored face. Picking greedily from the best
        # pair down can strand a query that a different pairing would have
        # served, so find the best assignment overall.
        if len(group_faces) < len(queries):
            continue
        weights = np.full((len(queries), len(group_faces)), _NO_MATCH)
        for similarity, query_pos, face_pos in pairs:
            weights[query_pos, face_pos] = similarity
        query_rows, face_cols = linear_sum_assignment(weights, maximize=True)
        assigned = weights[query_rows, face_cols]
        if assigned.min() == _NO_MATCH:
            continue
        framed_face = int(face_cols[assigned.argmax()])
        scored[group_id] = _GroupMatch(
            float(assigned.mean()),
            group_faces[framed_face].get("bbox"),
            len(queries),
        )
    return scored


def detect_faces_for_preview(image_path: str) -> DetectFacesResponse:
    """
    Lists the faces a search on this photo could use, without searching.

    The indices are the ones perform_face_search accepts as face_indices.
    """
    try:
        result = _detect_faces_cached(image_path)
    except Exception as e:
        return DetectFacesResponse(
            success=False, message=f"Failed to process image: {str(e)}"
        )
    if not result:
        return DetectFacesResponse(
            success=True, message="No faces detected in the image."
        )

    faces = [
        DetectedFace(index=index, bbox=BoundingBox(**bbox), confidence=confidence)
        for index, (bbox, confidence) in enumerate(
            zip(result["bboxes"], result["confidences"])
        )
    ]
    return DetectFacesResponse(
        success=True,
        message=(
            f"Detected {len(faces)} face{'' if len(faces) == 1 else 's'}."
            if faces
            else "No faces detected in the image."
        ),
        data=DetectFacesData(
            image_width=result["image_width"],
            image_height=result["image_height"],
            faces=faces,
            faces_skipped=result["faces_skipped"],
        ),
    )


def perform_face_search(
    image_path: str,
    face_indices: Optional[List[int]] = None,
    match_mode: str = "match_any",
) -> GetAllImagesResponse:
    """
    Performs face detection, embedding generation, and similarity search.

    Args:
        image_path (str): Path to the image file to process.
        face_indices (Optional[List[int]]): Faces of the photo to search with, as
            listed by detect_faces_for_preview. Defaults to the first face.
        match_mode (str): With several faces, "match_any" returns photos holding
            any of them and "match_all" only photos holding all of them.

    Returns:
        GetAllImagesResponse: Search result containing matched images.

    Raises:
        InvalidFaceSelection: A face index is outside the detected faces, or more
            than FACE_SEARCH_MAX_SELECTED_FACES distinct faces were selected.
    """
    try:
        result = _detect_faces_cached(image_path)
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

    face_count = len(result["embeddings"])
    selected = list(dict.fromkeys(face_indices)) if face_indices else [0]
    if len(selected) > FACE_SEARCH_MAX_SELECTED_FACES:
        raise InvalidFaceSelection(
            f"Select at most {FACE_SEARCH_MAX_SELECTED_FACES} faces at a time; "
            f"got {len(selected)}."
        )
    if any(index < 0 or index >= face_count for index in selected):
        raise InvalidFaceSelection(
            f"face_indices must be between 0 and {face_count - 1}; "
            f"the photo has {face_count} face(s)."
        )
    # The detector already ran FaceNet on these crops; no second model needed.
    queries = [result["embeddings"][index] for index in selected]

    image_faces = db_get_all_image_face_embeddings()
    video_faces = db_get_all_video_face_embeddings()
    if not image_faces and not video_faces:
        return GetAllImagesResponse(
            success=True,
            message="No face embeddings available for comparison.",
            data=[],
        )

    # A group photo holds several faces: rank each image by its best match
    # and frame that face, as is done per video below.
    by_image = _score_groups(queries, image_faces, "image_id", match_mode)
    ranked_images = sorted(by_image, key=lambda i: by_image[i].score, reverse=True)
    # Row by row: one unusable record must not hide every other match.
    matches: List[ImageData] = []
    for image in db_get_images_by_ids(ranked_images):
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
                    bboxes=by_image[image["id"]].bbox,
                    match_count=by_image[image["id"]].match_count,
                )
            )
        except ValidationError as e:
            logger.warning(f"Skipping image {image['id']}: {e}")

    # Several keyframe faces can belong to one video, so rank each video by
    # its best-matching face rather than listing it once per keyframe.
    by_video = _score_groups(queries, video_faces, "video_id", match_mode)
    ranked = sorted(by_video, key=lambda v: by_video[v].score, reverse=True)
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
