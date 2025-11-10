from fastapi import APIRouter, HTTPException, Query, status
from app.database.memories import (
    db_get_memories_on_this_day,
    db_get_recent_memories,
    db_get_memories_by_people,
    db_get_memories_by_tags,
)
from app.schemas.memories import (
    OnThisDayResponse,
    RecentMemoriesResponse,
    PeopleMemoriesResponse,
    TagMemoriesResponse,
    AllMemoriesResponse,
    AllMemoriesData,
    ErrorResponse,
)
from app.logging.setup_logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/on-this-day",
    response_model=OnThisDayResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_on_this_day_memories(
    years_back: int = Query(5, ge=1, le=20, description="Number of years to look back")
):
    """
    Get images from the same day in previous years.

    Returns memories from the same month and day across different years,
    creating a nostalgic "On This Day" experience.
    """
    try:
        memories = db_get_memories_on_this_day(years_back=years_back)

        return OnThisDayResponse(
            success=True,
            message=f"Successfully retrieved {len(memories)} 'On This Day' memories",
            data=memories,
        )
    except Exception as e:
        logger.error(f"Error getting 'On This Day' memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve 'On This Day' memories: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/recent",
    response_model=RecentMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_recent_memories(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    min_images: int = Query(
        5, ge=1, le=50, description="Minimum images per day to create a memory"
    ),
):
    """
    Get recent collections of images grouped by date.

    Returns memories from recent days where you took multiple photos,
    highlighting significant photo-taking events.
    """
    try:
        memories = db_get_recent_memories(days=days, min_images=min_images)

        return RecentMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {len(memories)} recent memories",
            data=memories,
        )
    except Exception as e:
        logger.error(f"Error getting recent memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve recent memories: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/people",
    response_model=PeopleMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_people_memories(
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of people to return"
    )
):
    """
    Get memories grouped by people (face clusters).

    Returns collections of photos featuring the same person,
    creating personalized memory collections.
    """
    try:
        memories = db_get_memories_by_people(limit=limit)

        return PeopleMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {len(memories)} people memories",
            data=memories,
        )
    except Exception as e:
        logger.error(f"Error getting people memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve people memories: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/tags",
    response_model=TagMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_tag_memories(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of tags to return")
):
    """
    Get memories grouped by common tags/objects.

    Returns collections of photos featuring the same objects or themes,
    creating thematic memory collections.
    """
    try:
        memories = db_get_memories_by_tags(limit=limit)

        return TagMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {len(memories)} tag memories",
            data=memories,
        )
    except Exception as e:
        logger.error(f"Error getting tag memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve tag memories: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/all",
    response_model=AllMemoriesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_memories(
    years_back: int = Query(
        5, ge=1, le=20, description="Years to look back for 'On This Day'"
    ),
    recent_days: int = Query(
        30, ge=1, le=365, description="Days to look back for recent memories"
    ),
    min_images: int = Query(
        5, ge=1, le=50, description="Minimum images per recent memory"
    ),
    people_limit: int = Query(
        10, ge=1, le=50, description="Maximum number of people memories"
    ),
    tags_limit: int = Query(
        10, ge=1, le=50, description="Maximum number of tag memories"
    ),
):
    """
    Get all types of memories in a single request.

    Returns a comprehensive collection including:
    - On This Day memories
    - Recent memories
    - People-based memories
    - Tag-based memories
    """
    try:
        on_this_day = db_get_memories_on_this_day(years_back=years_back)
        recent = db_get_recent_memories(days=recent_days, min_images=min_images)
        people = db_get_memories_by_people(limit=people_limit)
        tags = db_get_memories_by_tags(limit=tags_limit)

        total_memories = len(on_this_day) + len(recent) + len(people) + len(tags)

        return AllMemoriesResponse(
            success=True,
            message=f"Successfully retrieved {total_memories} total memories",
            data=AllMemoriesData(
                on_this_day=on_this_day,
                recent=recent,
                people=people,
                tags=tags,
            ),
        )
    except Exception as e:
        logger.error(f"Error getting all memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve memories: {str(e)}",
            ).model_dump(),
        )
