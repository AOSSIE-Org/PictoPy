from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.database.folders import (
    db_update_parent_ids_for_subtree,
    db_folder_exists,
    db_find_parent_folder_id,
    db_enable_ai_tagging_batch,
    db_disable_ai_tagging_batch,
)
from app.schemas.folders import (
    AddFolderRequest,
    AddFolderResponse,
    ErrorResponse,
    UpdateAITaggingRequest,
    UpdateAITaggingResponse,
)
import os
from app.utils.folders import folder_util_add_folder_tree
from concurrent.futures import ProcessPoolExecutor
from app.utils.images import image_util_process_folder_images, image_util_process_untagged_images
from app.utils.face_clusters import cluster_util_face_clusters_sync


router = APIRouter()


def post_folder_add_sequence(folder_path: str):
    """
    Post-addition sequence for a folder.
    This function is called after a folder is successfully added.
    It processes images in the folder and updates the database.
    """
    try:
        # Process images in the folder
        image_util_process_folder_images(folder_path)

    except Exception as e:
        print(f"Error in post processing after folder {folder_path} was added: {e}")
        return False
    return True


def post_AI_tagging_enabled_sequence():
    """
    Post-enabling AI tagging sequence.
    This function is called after AI tagging is enabled for a folder.
    It processes untagged images in the database.
    """
    try:
        image_util_process_untagged_images()
        cluster_util_face_clusters_sync()
    except Exception as e:
        print(f"Error in post processing after AI tagging was enabled: {e}")
        return False
    return True


def get_state(request: Request):
    return request.app.state


@router.post(
    "/add-folder",
    response_model=AddFolderResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 401, 409, 500]},
)
def add_folder(request: AddFolderRequest, app_state=Depends(get_state)):
    try:
        # Step 1: Data Validation

        if not os.path.isdir(request.folder_path):
            raise ValueError(f"Error: '{request.folder_path}' is not a valid directory.")

        if (
            not os.access(request.folder_path, os.R_OK)
            # Uncomment the following lines if you want to check for write and execute permissions
            # or not os.access(request.folder_path, os.W_OK)
            # or not os.access(request.folder_path, os.X_OK)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    success=False,
                    error="Permission denied",
                    message="The app does not have read permission for the specified folder",
                ),
            )

        request.folder_path = os.path.abspath(request.folder_path)

        # Step 2: Check if folder already exists
        if db_folder_exists(request.folder_path):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    success=False,
                    error="Folder Already Exists",
                    message=f"Folder '{request.folder_path}' is already in the database.",
                ).model_dump(),
            )

        # Step 3: If parent_folder_id not provided, try to find it
        parent_folder_id = request.parent_folder_id
        if parent_folder_id is None:
            parent_folder_id = db_find_parent_folder_id(request.folder_path)

        # Step 4: Add folder tree to database
        root_folder_id, folder_map = folder_util_add_folder_tree(
            root_path=request.folder_path,
            parent_folder_id=parent_folder_id,
            AI_Tagging=request.AI_Tagging or False,
            taggingCompleted=request.taggingCompleted,
        )

        # Step 5: Update parent ids for the subtree
        db_update_parent_ids_for_subtree(request.folder_path, folder_map)

        # Step 6: Process images in the folder
        executor: ProcessPoolExecutor = app_state.executor
        executor.submit(post_folder_add_sequence, request.folder_path)

        return AddFolderResponse(
            success=True,
            message=f"Successfully added folder tree starting at: {request.folder_path}",
            folder_id=root_folder_id,
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
                message=f"Unable to add folder: {str(e)}",
            ).model_dump(),
        )


@router.post(
    "/enable-ai-tagging",
    response_model=UpdateAITaggingResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def enable_ai_tagging(request: UpdateAITaggingRequest, app_state=Depends(get_state)):
    """Enable AI tagging for multiple folders."""
    try:
        if not request.folder_ids:
            raise ValueError("No folder IDs provided")

        updated_count = db_enable_ai_tagging_batch(request.folder_ids)

        executor: ProcessPoolExecutor = app_state.executor
        executor.submit(post_AI_tagging_enabled_sequence)

        return UpdateAITaggingResponse(
            success=True,
            message=f"Successfully enabled AI tagging for {updated_count} folder(s)",
            updated_count=updated_count,
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to enable AI tagging: {str(e)}",
            ).model_dump(),
        )


@router.post(
    "/disable-ai-tagging",
    response_model=UpdateAITaggingResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def disable_ai_tagging(request: UpdateAITaggingRequest):
    """Disable AI tagging for multiple folders."""
    try:
        if not request.folder_ids:
            raise ValueError("No folder IDs provided")

        updated_count = db_disable_ai_tagging_batch(request.folder_ids)

        return UpdateAITaggingResponse(
            success=True,
            message=f"Successfully disabled AI tagging for {updated_count} folder(s)",
            updated_count=updated_count,
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to disable AI tagging: {str(e)}",
            ).model_dump(),
        )
