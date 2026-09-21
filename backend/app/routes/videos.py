from concurrent.futures import Future, ProcessPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.datastructures import State
from typing import List, Optional
from pydantic import BaseModel

from app.database.video_frames import db_count_video_face_scan_progress
from app.database.videos import (
    db_get_all_videos,
    db_get_videos_by_ids,
    db_toggle_video_favourite_status,
    db_get_video_by_id,
)
from app.routes.dependencies import get_state
from app.schemas.videos import ErrorResponse, VideoData
from app.utils.videos import (
    video_util_backfill_video_faces,
    video_util_face_detection_enabled,
    video_util_to_video_data,
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


# Response Models
class GetAllVideosResponse(BaseModel):
    success: bool
    message: str
    data: List[VideoData]


@router.get(
    "/",
    response_model=GetAllVideosResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_videos():
    """Get all videos from the database."""
    try:
        video_data = video_util_to_video_data(db_get_all_videos())

        return GetAllVideosResponse(
            success=True,
            message=f"Successfully retrieved {len(video_data)} videos",
            data=video_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve videos: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/search",
    response_model=GetAllVideosResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def search_videos_by_tag(tag: str = Query(..., description="Tag name to search for")):
    """Search videos by tag name."""
    try:
        from app.database.video_frames import db_get_video_ids_by_tag

        video_data = video_util_to_video_data(
            db_get_videos_by_ids(db_get_video_ids_by_tag(tag))
        )

        return GetAllVideosResponse(
            success=True,
            message=f"Successfully retrieved {len(video_data)} videos for tag '{tag}'",
            data=video_data,
        )

    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Unable to search videos due to an internal error",
            ).model_dump(),
        )


class ScoredVideoData(VideoData):
    score: float
    # When in the video the best match was found -- what a future "jump to
    # this moment" deep link needs.
    best_frame_timestamp: Optional[float] = None


class SemanticSearchData(BaseModel):
    videos: List[ScoredVideoData]
    total: int


class SemanticSearchResponse(BaseModel):
    success: bool
    message: str
    data: SemanticSearchData


@router.get(
    "/semantic-search",
    response_model=SemanticSearchResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def semantic_search_videos(
    query: str = Query(..., min_length=1, description="Query text to search for")
):
    """Semantic search videos by query text using SigLIP2 keyframe embeddings."""
    try:
        import os
        import numpy as np

        from app.config.settings import (
            SIGLIP2_ACTIVE_CHECKPOINT,
            SIGLIP2_SCORING_METADATA,
            SIGLIP2_MATCH_THRESHOLD,
            SIGLIP2_QUERY_TEMPLATE,
        )
        from app.database.video_frames import db_get_all_frame_embeddings
        from app.models.model_registry import (
            get_siglip2_registry_keys,
            get_siglip2_tokenizer_key,
            get_model_path,
        )
        from app.utils.SigLIP import (
            siglip_util_tokenize_query,
            siglip_util_get_text_model,
        )

        _, text_key = get_siglip2_registry_keys(SIGLIP2_ACTIVE_CHECKPOINT)
        tokenizer_key = get_siglip2_tokenizer_key(SIGLIP2_ACTIVE_CHECKPOINT)
        text_model_path = get_model_path(text_key)
        tokenizer_model_path = get_model_path(tokenizer_key)

        for path, missing in (
            (text_model_path, "SigLIP2 text model"),
            (tokenizer_model_path, "SigLIP2 tokenizer"),
        ):
            if not os.path.exists(path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        success=False,
                        error="Not Found",
                        message=f"semantic search unavailable: {missing} not installed",
                    ).model_dump(),
                )

        metadata = SIGLIP2_SCORING_METADATA[SIGLIP2_ACTIVE_CHECKPOINT]
        video_ids, timestamps, frame_matrix = db_get_all_frame_embeddings(
            metadata["model_version"]
        )

        if not video_ids:
            return SemanticSearchResponse(
                success=True,
                message="No video frames have been embedded yet.",
                data=SemanticSearchData(videos=[], total=0),
            )

        text_model = siglip_util_get_text_model(text_model_path, text_key)
        input_ids, attention_mask = siglip_util_tokenize_query(
            SIGLIP2_QUERY_TEMPLATE.format(query=query)
        )
        query_vector = np.asarray(
            text_model.get_embedding(input_ids, attention_mask), dtype=np.float32
        ).flatten()

        logits = (
            frame_matrix @ query_vector * np.exp(metadata["logit_scale"])
            + metadata["logit_bias"]
        )
        scores = 1.0 / (1.0 + np.exp(-logits))

        # Max-pool per video: a video matches as well as its best frame does.
        best: dict = {}
        for i, video_id in enumerate(video_ids):
            score = float(scores[i])
            if score < SIGLIP2_MATCH_THRESHOLD:
                continue
            if video_id not in best or score > best[video_id][0]:
                best[video_id] = (score, timestamps[i])

        ranked = sorted(best.items(), key=lambda item: item[1][0], reverse=True)
        # Keyed rather than zipped: db_get_videos_by_ids drops IDs it can't
        # find, which would silently shift every score onto the wrong video.
        by_id = {
            video.id: video
            for video in video_util_to_video_data(
                db_get_videos_by_ids([video_id for video_id, _ in ranked])
            )
        }

        scored = [
            ScoredVideoData(
                **by_id[video_id].model_dump(),
                score=score,
                best_frame_timestamp=timestamp,
            )
            for video_id, (score, timestamp) in ranked
            if video_id in by_id
        ]

        return SemanticSearchResponse(
            success=True,
            message=f"Found {len(scored)} matching videos",
            data=SemanticSearchData(videos=scored, total=len(scored)),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in video semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to search videos: {str(e)}",
            ).model_dump(),
        )


def post_video_face_scan_sequence() -> bool:
    """Scan already-tagged videos for people, then join what it finds to the
    photo clusters. Module-level so the process pool can pickle it."""
    from app.utils.face_clusters import cluster_util_attach_keyframe_faces

    try:
        video_util_backfill_video_faces()
        cluster_util_attach_keyframe_faces()
    except Exception:
        logger.exception("Error scanning videos for faces")
        return False
    return True


class FaceScanStatusData(BaseModel):
    total: int
    scanned: int
    pending: int
    # State of the scan started from Settings; a sync's own pass isn't tracked
    running: bool = False
    failed: bool = False


class FaceScanStatusResponse(BaseModel):
    success: bool
    message: str
    data: FaceScanStatusData


def _face_scan_status(app_state: State) -> FaceScanStatusData:
    total, scanned = db_count_video_face_scan_progress()
    scan: Optional[Future] = getattr(app_state, "video_face_scan", None)
    running = scan is not None and not scan.done()
    failed = (
        scan is not None
        and scan.done()
        and (scan.cancelled() or scan.exception() is not None or not scan.result())
    )
    return FaceScanStatusData(
        total=total,
        scanned=scanned,
        pending=total - scanned,
        running=running,
        failed=failed,
    )


@router.post(
    "/scan-faces",
    response_model=FaceScanStatusResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def scan_video_faces(
    app_state: State = Depends(get_state),
) -> FaceScanStatusResponse:
    """Start a background pass over videos tagged before finding people in
    videos was turned on. Returns how many it has to get through."""
    try:
        if not video_util_face_detection_enabled():
            raise ValueError(
                "Turn on 'Find People in Videos' in Settings before scanning"
            )

        # Kept on app state so the status endpoint can report a running or
        # failed scan; a second click while one is running is a no-op.
        if not _face_scan_status(app_state).running:
            executor: ProcessPoolExecutor = app_state.executor
            app_state.video_face_scan = executor.submit(post_video_face_scan_sequence)

        status_data = _face_scan_status(app_state)
        return FaceScanStatusResponse(
            success=True,
            message=f"Scanning {status_data.pending} video(s) for people",
            data=status_data,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="Validation Error",
                message=str(e),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error starting the video face scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to start the video face scan: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/face-scan-status",
    response_model=FaceScanStatusResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_video_face_scan_status(
    app_state: State = Depends(get_state),
) -> FaceScanStatusResponse:
    """How far the face scan has got, for a caller polling its progress."""
    try:
        status_data = _face_scan_status(app_state)
        return FaceScanStatusResponse(
            success=True,
            message=f"{status_data.scanned} of {status_data.total} video(s) scanned",
            data=status_data,
        )

    except Exception as e:
        logger.error(f"Error reading the video face scan status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to read the video face scan status: {str(e)}",
            ).model_dump(),
        )


class PurgeFrameCacheResponse(BaseModel):
    success: bool
    message: str
    bytes_reclaimed: int


@router.post(
    "/purge-frame-cache",
    response_model=PurgeFrameCacheResponse,
    responses={500: {"model": ErrorResponse}},
)
def purge_frame_cache():
    """Delete the sampled keyframe JPEGs. Tags and semantic search survive:
    only the on-disk frames are removed, not their embeddings."""
    try:
        from app.utils.videos import video_util_purge_frame_cache

        reclaimed = video_util_purge_frame_cache()
        return PurgeFrameCacheResponse(
            success=True,
            message=f"Reclaimed {reclaimed} bytes of video frame cache",
            bytes_reclaimed=reclaimed,
        )
    except Exception as e:
        logger.error(f"Error purging video frame cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to purge video frame cache: {str(e)}",
            ).model_dump(),
        )


class ToggleFavouriteRequest(BaseModel):
    video_id: str


class ToggleFavouriteResponse(BaseModel):
    success: bool
    video_id: str
    isFavourite: bool


@router.post(
    "/toggle-favourite",
    response_model=ToggleFavouriteResponse,
    responses={code: {"model": ErrorResponse} for code in [404, 500]},
)
def toggle_favourite(req: ToggleFavouriteRequest):
    """
    Toggle the favorite status of a video.
    """
    video_id = req.video_id
    try:
        success = db_toggle_video_favourite_status(video_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Video not found",
                    message=f"No video with id '{video_id}' could be toggled",
                ).model_dump(),
            )
        # Fetch updated status to return
        video = db_get_video_by_id(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Video not found",
                    message=f"Video '{video_id}' disappeared after toggling",
                ).model_dump(),
            )
        return {
            "success": True,
            "video_id": video_id,
            "isFavourite": video.get("isFavourite", False),
        }
    except HTTPException:
        raise  # Re-raise HTTPExceptions to preserve status codes
    except Exception as e:
        logger.error(f"error in /toggle-favourite route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to toggle favourite: {str(e)}",
            ).model_dump(),
        )
