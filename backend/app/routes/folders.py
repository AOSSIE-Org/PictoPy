from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Tuple
from app.database.folders import (
    db_update_parent_ids_for_subtree,
    db_folder_exists,
    db_find_parent_folder_id,
    db_enable_ai_tagging_batch,
    db_disable_ai_tagging_batch,
    db_delete_folders_batch,
    db_get_direct_child_folders,
    db_get_folder_ids_by_path_prefix,
    db_get_all_folder_details,
)
from app.logging.setup_logging import get_logger
from app.schemas.folders import (
    AddFolderRequest,
    AddFolderResponse,
    AddFolderData,
    ErrorResponse,
    UpdateAITaggingRequest,
    UpdateAITaggingResponse,
    UpdateAITaggingData,
    DeleteFoldersRequest,
    DeleteFoldersResponse,
    DeleteFoldersData,
    SyncFolderRequest,
    SyncFolderResponse,
    SyncFolderData,
    GetAllFoldersResponse,
    GetAllFoldersData,
    FolderDetails,
)
import os
from app.utils.folders import (
    folder_util_add_folder_tree,
    folder_util_add_multiple_folder_trees,
    folder_util_delete_obsolete_folders,
    folder_util_get_filesystem_direct_child_folders,
)
from concurrent.futures import ProcessPoolExecutor
from app.utils.images import (
    image_util_process_folder_images,
    image_util_process_untagged_images,
)
from app.utils.face_clusters import cluster_util_face_clusters_sync
from app.utils.API import API_util_restart_sync_microservice_watcher

# Initialize logger
logger = get_logger(__name__)

router = APIRouter()


def post_folder_add_sequence(folder_path: str, folder_id: int):
    """
    Post-addition sequence for a folder.
    This function is called after a folder is successfully added.
    It processes images in the folder and updates the database.
    """
    try:
        # Get all folder IDs and paths that match the root path prefix
        folder_data = []
        folder_ids_and_paths = db_get_folder_ids_by_path_prefix(folder_path)

        # Set all folders to non-recursive (False)
        for folder_id_from_db, folder_path_from_db in folder_ids_and_paths:
            folder_data.append((folder_path_from_db, folder_id_from_db, False))

        logger.info(f"Add folder: {folder_data}")
        # Process images in all folders
        image_util_process_folder_images(folder_data)
        image_util_process_untagged_images()
        cluster_util_face_clusters_sync(force_full_reclustering=True)  # Force full reclustering for new photos

        # Restart sync microservice watcher after processing images
        API_util_restart_sync_microservice_watcher()

    except Exception as e:
        logger.error(
            f"Error in post processing after folder {folder_path} was added: {e}"
        )
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
        logger.error(f"Error in post processing after AI tagging was enabled: {e}")
        return False
    return True


def post_sync_folder_sequence(
    folder_path: str, folder_id: int, added_folders: List[Tuple[str, str]]
):
    """
    Post-sync sequence for a folder.
    This function is called after a folder is synced.
    It processes images in the folder and updates the database.
    """
    try:
        # Create folder data array
        folder_data = []

        folder_data.append((folder_path, folder_id, False))

        for added_folder_id, added_folder_path in added_folders:
            folder_data.append((added_folder_path, added_folder_id, False))

        logger.info(f"Sync folder: {folder_data}")
        # Process images in all folders
        image_util_process_folder_images(folder_data)
        image_util_process_untagged_images()
        cluster_util_face_clusters_sync(force_full_reclustering=True)  # Force full reclustering for synced photos

        # Restart sync microservice watcher after processing images
        API_util_restart_sync_microservice_watcher()
    except Exception as e:
        logger.error(
            f"Error in post processing after folder {folder_path} was synced: {e}"
        )
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
            raise ValueError(
                f"Error: '{request.folder_path}' is not a valid directory."
            )

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
                ).model_dump(),
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
            AI_Tagging=True,  # Enable AI tagging by default for automatic face detection
            taggingCompleted=request.taggingCompleted,
        )

        # Step 5: Update parent ids for the subtree
        db_update_parent_ids_for_subtree(request.folder_path, folder_map)

        # Step 6: Call the post-addition sequence in a separate process
        executor: ProcessPoolExecutor = app_state.executor
        executor.submit(post_folder_add_sequence, request.folder_path, root_folder_id)

        return AddFolderResponse(
            data=AddFolderData(
                folder_id=root_folder_id, folder_path=request.folder_path
            ),
            success=True,
            message=f"Successfully added folder tree starting at: {request.folder_path}",
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
            data=UpdateAITaggingData(
                updated_count=updated_count, folder_ids=request.folder_ids
            ),
            success=True,
            message=f"Successfully enabled AI tagging for {updated_count} folder(s)",
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
            data=UpdateAITaggingData(
                updated_count=updated_count, folder_ids=request.folder_ids
            ),
            success=True,
            message=f"Successfully disabled AI tagging for {updated_count} folder(s)",
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


@router.delete(
    "/delete-folders",
    response_model=DeleteFoldersResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def delete_folders(request: DeleteFoldersRequest):
    """Delete multiple folders by their IDs."""
    try:
        if not request.folder_ids:
            raise ValueError("No folder IDs provided")

        deleted_count = db_delete_folders_batch(request.folder_ids)

        return DeleteFoldersResponse(
            data=DeleteFoldersData(
                deleted_count=deleted_count, folder_ids=request.folder_ids
            ),
            success=True,
            message=f"Successfully deleted {deleted_count} folder(s)",
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
                message=f"Unable to delete folders: {str(e)}",
            ).model_dump(),
        )


@router.post(
    "/sync-folder",
    response_model=SyncFolderResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def sync_folder(request: SyncFolderRequest, app_state=Depends(get_state)):
    """Sync a folder by comparing filesystem folders with database entries and removing extra DB entries."""
    try:
        # Step 1: Get current state from both sources
        db_child_folders = db_get_direct_child_folders(request.folder_id)
        filesystem_folders = folder_util_get_filesystem_direct_child_folders(
            request.folder_path
        )

        # Step 2: Compare and identify differences
        filesystem_folder_set = set(filesystem_folders)
        db_folder_paths = {folder_path for folder_id, folder_path in db_child_folders}

        folders_to_delete = db_folder_paths - filesystem_folder_set
        folders_to_add = filesystem_folder_set - db_folder_paths

        # Step 3: Perform synchronization operations
        deleted_count, deleted_folders = folder_util_delete_obsolete_folders(
            db_child_folders, folders_to_delete
        )
        added_count, added_folders_with_ids = folder_util_add_multiple_folder_trees(
            folders_to_add, request.folder_id
        )

        # Extract just the paths for the API response
        added_folders = [
            folder_path for folder_id, folder_path in added_folders_with_ids
        ]

        executor: ProcessPoolExecutor = app_state.executor
        executor.submit(
            post_sync_folder_sequence,
            request.folder_path,
            request.folder_id,
            added_folders_with_ids,
        )
        # Step 4: Return comprehensive response
        return SyncFolderResponse(
            data=SyncFolderData(
                deleted_count=deleted_count,
                deleted_folders=deleted_folders,
                added_count=added_count,
                added_folders=added_folders,
                folder_id=request.folder_id,
                folder_path=request.folder_path,
            ),
            success=True,
            message=f"Successfully synced folder. Added {added_count} folder(s), deleted {deleted_count} folder(s)",
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
                message=f"Unable to sync folder: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/all-folders",
    response_model=GetAllFoldersResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_all_folders():
    """Get details of all folders in the database."""
    try:
        folder_details_raw = db_get_all_folder_details()

        # Convert raw tuples to FolderDetails objects
        folders = []
        for folder_data in folder_details_raw:
            (
                folder_id,
                folder_path,
                parent_folder_id,
                last_modified_time,
                ai_tagging,
                tagging_completed,
            ) = folder_data
            folders.append(
                FolderDetails(
                    folder_id=folder_id,
                    folder_path=folder_path,
                    parent_folder_id=parent_folder_id,
                    last_modified_time=last_modified_time,
                    AI_Tagging=ai_tagging,
                    taggingCompleted=tagging_completed,
                )
            )

        return GetAllFoldersResponse(
            data=GetAllFoldersData(folders=folders, total_count=len(folders)),
            success=True,
            message=f"Successfully retrieved {len(folders)} folder(s)",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve folders: {str(e)}",
            ).model_dump(),
        )
