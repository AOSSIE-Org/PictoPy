from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from app.database.metadata import db_get_metadata, db_update_metadata
from app.logging.setup_logging import get_logger
from app.schemas.user_preferences import (
    GetUserPreferencesResponse,
    UpdateUserPreferencesRequest,
    UpdateUserPreferencesResponse,
    UserPreferencesData,
    ErrorResponse,
)

router = APIRouter()
logger = get_logger(__name__)


def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge nested dicts recursively; scalars in `updates` win."""
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_preferences(metadata: Optional[Dict[str, Any]]) -> UserPreferencesData:
    """
    Build preferences from the stored blob, falling back to defaults.

    Stored values predate newer fields and may be stale or hand-edited, so a
    validation failure yields defaults rather than a 500.
    """
    stored = (metadata or {}).get("user_preferences") or {}
    try:
        return UserPreferencesData.model_validate(stored)
    except ValueError as e:
        logger.warning(f"Stored user preferences are invalid, using defaults: {e}")
        return UserPreferencesData()


@router.get(
    "/",
    response_model=GetUserPreferencesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_user_preferences():
    """Get user preferences from metadata."""
    try:
        return GetUserPreferencesResponse(
            success=True,
            message="Successfully retrieved user preferences",
            user_preferences=_load_preferences(db_get_metadata()),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve user preferences: {str(e)}",
            ).model_dump(),
        )


@router.put(
    "/",
    response_model=UpdateUserPreferencesResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def update_user_preferences(request: UpdateUserPreferencesRequest):
    """Update user preferences in metadata."""
    try:
        # exclude_unset keeps this a genuine partial update: fields the caller
        # omitted are absent, not None, so they never overwrite stored values.
        updates = request.model_dump(exclude_unset=True, exclude_none=True)
        if not updates:
            raise ValueError("At least one preference field must be provided")

        metadata = db_get_metadata() or {}
        current = metadata.get("user_preferences") or {}
        merged = _deep_merge(current, updates)

        # Validate the merged result, not the patch: bounds like
        # max_images >= min_images span fields the caller may not have sent.
        user_preferences = UserPreferencesData.model_validate(merged)

        metadata["user_preferences"] = merged
        if not db_update_metadata(metadata):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    success=False,
                    error="Update Failed",
                    message="Failed to update user preferences.",
                ).model_dump(),
            )

        return UpdateUserPreferencesResponse(
            success=True,
            message="Successfully updated user preferences",
            user_preferences=user_preferences,
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
    except HTTPException as e:
        # Re-raise HTTPExceptions to preserve the status code and detail
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to update user preferences: {str(e)}",
            ).model_dump(),
        )
