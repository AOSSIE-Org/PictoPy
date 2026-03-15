"""
Semantic search routes
======================

Prefix: ``/search``

Endpoints
---------
GET  /search/semantic          – query the semantic index
GET  /search/index-status      – inspect index health / size
POST /search/index             – trigger incremental (or full) re-indexing
DELETE /search/index/{image_id} – remove one image from the index
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.ai.search_service import SearchService
from app.schemas.search import (
    IndexStatusResponse,
    IndexTriggerResponse,
    SemanticSearchResponse,
    SearchResultItem,
)
from app.config.settings import SEARCH_DEFAULT_TOP_K, SEARCH_MIN_SCORE
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------


def _get_service(request: Request) -> SearchService:
    """Retrieve the singleton SearchService from application state."""
    service: Optional[SearchService] = getattr(
        request.app.state, "search_service", None
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search service is not initialised.",
        )
    return service


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic image search",
    description=(
        "Search for images using a natural-language query.  The query is mapped "
        "onto the same fixed-dimension embedding space used to index image "
        "metadata (object classes, date/time, season, faces, GPS) and the "
        "most similar images are returned ranked by cosine similarity."
    ),
)
def semantic_search(
    request: Request,
    q: str = Query(..., min_length=1, description="Free-text search query."),
    limit: int = Query(
        default=SEARCH_DEFAULT_TOP_K,
        ge=1,
        le=200,
        description="Maximum number of results to return.",
    ),
    min_score: float = Query(
        default=SEARCH_MIN_SCORE,
        ge=0.0,
        le=1.0,
        description="Minimum cosine-similarity score threshold.",
    ),
) -> SemanticSearchResponse:
    service = _get_service(request)
    try:
        raw_results = service.search(q, top_k=limit, min_score=min_score)
    except Exception:
        logger.exception("Semantic search failed for query %r", q)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Semantic search failed.",
        )

    items = [
        SearchResultItem(
            image_id=r.image_id,
            score=r.score,
            path=r.path,
            thumbnail_path=r.thumbnail_path,
            tags=r.tags,
        )
        for r in raw_results
    ]
    return SemanticSearchResponse(
        success=True,
        query=q,
        total=len(items),
        results=items,
    )


@router.get(
    "/index-status",
    response_model=IndexStatusResponse,
    summary="Inspect semantic index status",
)
def index_status(request: Request) -> IndexStatusResponse:
    service = _get_service(request)
    return IndexStatusResponse(
        success=True,
        indexed_count=service.index_size,
        is_loaded=service.is_index_loaded,
    )


@router.post(
    "/index",
    response_model=IndexTriggerResponse,
    summary="Trigger semantic indexing",
    description=(
        "Index all tagged images that do not yet have a stored embedding.  "
        "Pass ``force=true`` to re-embed every image (useful after a settings "
        "change such as increasing ``MAX_FACE_CLUSTERS``)."
    ),
)
def trigger_index(
    request: Request,
    force: bool = Query(
        default=False,
        description="Re-index all images even if already indexed.",
    ),
) -> IndexTriggerResponse:
    service = _get_service(request)
    try:
        count = service.index_all(force=force)
    except Exception:
        logger.exception("Indexing failed (force=%s)", force)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Indexing operation failed.",
        )
    return IndexTriggerResponse(
        success=True,
        message=(
            f"Indexed {count} new image(s)."
            if count
            else "All images are already indexed."
        ),
        newly_indexed=count,
    )


@router.delete(
    "/index/{image_id}",
    response_model=IndexTriggerResponse,
    summary="Remove an image from the semantic index",
    description=(
        "Remove the embedding for *image_id* from both the persistent store "
        "and the in-memory index.  Call this when an image is deleted from "
        "the library so it no longer appears in search results."
    ),
)
def remove_from_index(
    image_id: str,
    request: Request,
) -> IndexTriggerResponse:
    service = _get_service(request)
    try:
        service.remove_image(image_id)
    except Exception:
        logger.exception("Failed to remove image %s from index", image_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not remove image {image_id} from the index.",
        )
    return IndexTriggerResponse(
        success=True,
        message=f"Image {image_id} removed from the semantic index.",
        newly_indexed=0,
    )
