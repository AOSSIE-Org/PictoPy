import os
from concurrent.futures import Future, ProcessPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.datastructures import State

from app.database.folders import (
    INDEXING_COMPLETED,
    INDEXING_IN_PROGRESS,
    INDEXING_INTERRUPTED,
    db_delete_folders_batch,
    db_disable_ai_tagging_batch,
    db_enable_ai_tagging_batch,
    db_find_parent_folder_id,
    db_folder_exists,
    db_get_all_folder_details,
    db_get_direct_child_folders,
    db_get_folder_ids_by_path_prefix,
    db_set_tagging_completed,
    db_update_folder_indexing_status,
    db_update_parent_ids_for_subtree,
)
from app.logging.setup_logging import get_logger
from app.routes.dependencies import get_state
from app.schemas.folders import (
    AddFolderData,
    AddFolderRequest,
    AddFolderResponse,
    DeleteFoldersData,
    DeleteFoldersRequest,
    DeleteFoldersResponse,
    ErrorResponse,
    FolderDetails,
    GetAllFoldersData,
    GetAllFoldersResponse,
    SyncFolderData,
    SyncFolderRequest,
    SyncFolderResponse,
    UpdateAITaggingData,
    UpdateAITaggingRequest,
    UpdateAITaggingResponse,
)
from app.utils.API import API_util_restart_sync_microservice_watcher
from app.utils.face_clusters import cluster_util_face_clusters_sync
from app.utils.folders import (
    folder_util_add_folder_tree,
    folder_util_add_multiple_folder_trees,
    folder_util_delete_obsolete_folders,
    folder_util_get_filesystem_direct_child_folders,
)
from app.utils.images import (
    image_util_process_folder_images,
    image_util_process_unembedded_images,
    image_util_process_untagged_images,
)
from app.utils.model_bootstrap import ensure_ai_tagging_models
from app.utils.semantic_labels import (
    semantic_util_score_images,
    semantic_util_score_videos,
)
from app.utils.videos import (
    video_util_process_folder_videos,
    video_util_process_unembedded_frames,
    video_util_process_untagged_videos,
)

# Initialize logger
logger = get_logger(__name__)

router = APIRouter()


def _curate_memories(trigger: str) -> None:
    """
    Refresh memories after the library changed.

    Imported late to keep the curator out of the module import graph, and
    swallowed on failure: a curation problem must never fail an import.

    Never forced: force is what overrides the user's memories preference, and
    a background import is not the user asking for memories.
    """
    try:
        from app.utils.memory_curator import memory_curator_run

        memory_curator_run(trigger=trigger)
    except Exception as e:
        logger.error(f"Memory curation failed after {trigger}: {e}")


def _queue_post_index_tagging_sweep(index_future: Future, app_state: State) -> None:
    """
    Runs after folder indexing completes to trigger a follow-up tagging sweep.
    Prevents images indexed after an earlier tagging pass from being missed.
    """
    try:
        if index_future.result() is not True:
            logger.warning(
                "Skipping post-index tagging sweep: indexing did not complete"
            )
            return
        app_state.executor.submit(post_AI_tagging_enabled_sequence)
    except Exception as e:
        logger.error(f"Failed to queue post-index tagging sweep: {e}")


def post_folder_add_sequence(folder_path: str, folder_id: int):
    """
    Post-addition sequence for a folder.
    This function is called after a folder is successfully added.
    It processes images in the folder and updates the database.
    """
    folder_ids_and_paths = []
    try:
        # Get all folder IDs and paths that match the root path prefix
        folder_data = []
        folder_ids_and_paths = db_get_folder_ids_by_path_prefix(folder_path)

        # Set all folders to non-recursive (False)
        for folder_id_from_db, folder_path_from_db in folder_ids_and_paths:
            folder_data.append((folder_path_from_db, folder_id_from_db, False))

            db_update_folder_indexing_status(folder_id_from_db, INDEXING_IN_PROGRESS)

        logger.info(f"Add folder: {folder_data}")
        # Process images and videos in all folders
        image_util_process_folder_images(folder_data)
        video_util_process_folder_videos(folder_data)

        # Restart sync microservice watcher after processing images
        API_util_restart_sync_microservice_watcher()

        for folder_id_from_db, _ in folder_ids_and_paths:
            db_update_folder_indexing_status(folder_id_from_db, INDEXING_COMPLETED)

        # No AI has run yet, so only the date-driven triggers can produce
        # anything here. Semantic events appear once tagging is enabled and
        # this runs again.
        _curate_memories("folder_add")

    except Exception as e:
        logger.error(
            f"Error in post processing after folder {folder_path} was added: {e}"
        )
        # The walk stopped partway, so the folder is not indexed. Clearing the
        # busy flag as 'completed' would claim a file set that was never read.
        for folder_id_from_db, _ in folder_ids_and_paths:
            db_update_folder_indexing_status(folder_id_from_db, INDEXING_INTERRUPTED)
        return False
    return True


def post_AI_tagging_enabled_sequence():
    """
    Post-enabling AI tagging sequence.
    This function is called after AI tagging is enabled for a folder.
    It processes untagged images in the database.
    """
    try:
        db_set_tagging_completed(False)
        ensure_ai_tagging_models()
        image_util_process_untagged_images()
        cluster_util_face_clusters_sync()
        image_util_process_unembedded_images()
        semantic_util_score_images()
        # Curate before the video pass: semantic labels are written by now,
        # and the video pass can run for minutes.
        _curate_memories("ai_tagging")
        # Videos last: photos are the primary surface, so they finish first.
        video_util_process_untagged_videos()
        video_util_process_unembedded_frames()
        semantic_util_score_videos()
    except Exception as e:
        logger.error(f"Error in post processing after AI tagging was enabled: {e}")
        return False
    finally:
        # Set even on failure. A folder that failed to tag is not still
        # tagging, and leaving the flag clear would block memories forever.
        db_set_tagging_completed(True)
    return True


def post_sync_folder_sequence(
    folder_path: str, folder_id: int, added_folders: list[tuple[str, str]]
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
        db_set_tagging_completed(False)
        # Process images and videos in all folders
        image_util_process_folder_images(folder_data)
        video_util_process_folder_videos(folder_data)
        image_util_process_untagged_images()
        cluster_util_face_clusters_sync()
        image_util_process_unembedded_images()
        semantic_util_score_images()
        _curate_memories("sync_folder")
        video_util_process_untagged_videos()
        video_util_process_unembedded_frames()
        semantic_util_score_videos()

        # Restart sync microservice watcher after processing images
        API_util_restart_sync_microservice_watcher()
    except Exception as e:
        logger.error(
            f"Error in post processing after folder {folder_path} was synced: {e}"
        )
        return False
    finally:
        db_set_tagging_completed(True)
    return True


@router.post(
    "/add-folder",
    response_model=AddFolderResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 401, 409, 500]},
)
def add_folder(request: AddFolderRequest, app_state: State = Depends(get_state)):
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
            AI_Tagging=False,
            taggingCompleted=request.taggingCompleted,
        )

        # Step 5: Update parent ids for the subtree
        db_update_parent_ids_for_subtree(request.folder_path, folder_map)

        # Step 6: Call the post-addition sequence in a separate process.
        # Own pool so this never waits on another folder's AI tagging.
        indexing_executor: ProcessPoolExecutor = app_state.indexing_executor
        index_future = indexing_executor.submit(
            post_folder_add_sequence, request.folder_path, root_folder_id
        )
        # Also queue a catch-up tagging sweep for once indexing lands. Needed
        # because indexing and tagging are now on separate pools: if the AI
        # pool is free, a sweep can start (and finish, finding nothing) before
        # this folder's images are even in the DB - see the callback docstring.
        index_future.add_done_callback(
            lambda future: _queue_post_index_tagging_sweep(future, app_state)
        )

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
                message=f"Unable to add folder: {e!s}",
            ).model_dump(),
        )


@router.post(
    "/enable-ai-tagging",
    response_model=UpdateAITaggingResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def enable_ai_tagging(
    request: UpdateAITaggingRequest, app_state: State = Depends(get_state)
):
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
                message=f"Unable to enable AI tagging: {e!s}",
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
                message=f"Unable to disable AI tagging: {e!s}",
            ).model_dump(),
        )


@router.delete(
    "/delete-folders",
    response_model=DeleteFoldersResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def delete_folders(
    request: DeleteFoldersRequest, app_state: State = Depends(get_state)
):
    """Delete multiple folders by their IDs."""
    try:
        if not request.folder_ids:
            raise ValueError("No folder IDs provided")

        deleted_count = db_delete_folders_batch(request.folder_ids)

        # Synchronous so the response can't race the frontend's next
        # Memories fetch; imported late, like _curate_memories below.
        try:
            from app.utils.memory_curator import memory_curator_prune_empty

            memory_curator_prune_empty()
        except Exception:
            logger.exception("Failed to prune empty memories after folder delete")

        # New memories from what's left can still be found in the
        # background -- best-effort, a dropped submit just delays it.
        executor: ProcessPoolExecutor = app_state.executor
        try:
            executor.submit(_curate_memories, "folder_delete")
        except Exception:
            logger.exception("Failed to queue memory curation after folder delete")

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
                message=f"Unable to delete folders: {e!s}",
            ).model_dump(),
        )


@router.post(
    "/sync-folder",
    response_model=SyncFolderResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def sync_folder(request: SyncFolderRequest, app_state: State = Depends(get_state)):
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
                message=f"Unable to sync folder: {e!s}",
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
                indexing_status,
                image_count,
                video_count,
            ) = folder_data
            folders.append(
                FolderDetails(
                    folder_id=folder_id,
                    folder_path=folder_path,
                    parent_folder_id=parent_folder_id,
                    last_modified_time=last_modified_time,
                    AI_Tagging=ai_tagging,
                    taggingCompleted=tagging_completed,
                    indexing_status=indexing_status,
                    image_count=image_count,
                    video_count=video_count,
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
                message=f"Unable to retrieve folders: {e!s}",
            ).model_dump(),
        )
