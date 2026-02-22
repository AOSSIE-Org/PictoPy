from fastapi import APIRouter, HTTPException, status
from app.database.metadata import db_get_metadata, db_update_metadata
from app.schemas.user_preferences import (
    GetUserPreferencesResponse,
    UpdateUserPreferencesRequest,
    UpdateUserPreferencesResponse,
    UserPreferencesData,
    ErrorResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=GetUserPreferencesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_user_preferences():
    """Get user preferences from metadata."""
    try:
        metadata = db_get_metadata()

        # Get user_preferences from metadata or use defaults
        user_prefs_data = {}
        if metadata and "user_preferences" in metadata:
            user_prefs_data = metadata["user_preferences"]

        # Create UserPreferencesData with defaults for missing values
        user_preferences = UserPreferencesData(
            YOLO_model_size=user_prefs_data.get("YOLO_model_size", "small"),
            GPU_Acceleration=user_prefs_data.get("GPU_Acceleration", True),
        )

        return GetUserPreferencesResponse(
            success=True,
            message="Successfully retrieved user preferences",
            user_preferences=user_preferences,
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
        # Step 1: Validate that at least one field is provided
        if request.YOLO_model_size is None and request.GPU_Acceleration is None:
            raise ValueError("At least one preference field must be provided")

        # Step 2: Get current metadata
        metadata = db_get_metadata() or {}

        # Step 3: Get current user preferences or create new ones
        current_user_prefs = metadata.get("user_preferences", {})

        # Step 4: Update only provided fields
        if request.YOLO_model_size is not None:
            current_user_prefs["YOLO_model_size"] = request.YOLO_model_size

        if request.GPU_Acceleration is not None:
            current_user_prefs["GPU_Acceleration"] = request.GPU_Acceleration

        # Step 5: Update metadata with new user preferences
        metadata["user_preferences"] = current_user_prefs

        # Step 6: Save to database
        updated = db_update_metadata(metadata)

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    success=False,
                    error="Update Failed",
                    message="Failed to update user preferences.",
                ).model_dump(),
            )

        # Step 7: Create response with updated preferences
        user_preferences = UserPreferencesData(
            YOLO_model_size=current_user_prefs.get("YOLO_model_size", "small"),
            GPU_Acceleration=current_user_prefs.get("GPU_Acceleration", True),
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
