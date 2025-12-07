import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import {
  enableAITagging,
  getAllFolders,
  disableAITagging,
  deleteFolders,
} from '@/api/api-functions';
import { selectAllFolders } from '@/features/folderSelectors';
import { setFolders, setTaggingStatus } from '@/features/folderSlice';
import { FolderDetails } from '@/types/Folder';
import { useMutationFeedback } from './useMutationFeedback';
import { addWsListener } from '@/lib/ws';
import { FolderTaggingInfo } from '@/types/FolderStatus';

/**
 * Custom hook for folder operations
 * Manages folder queries, AI tagging mutations, and folder deletion
 */
export const useFolderOperations = () => {
  const dispatch = useDispatch();
  const folders = useSelector(selectAllFolders);

  // Query for folders (initial load only, no polling)
  const foldersQuery = usePictoQuery({
    queryKey: ['folders'],
    queryFn: getAllFolders,
  });

  // Apply feedback to the folders query
  useMutationFeedback(
    {
      isPending: foldersQuery.isLoading,
      isSuccess: foldersQuery.isSuccess,
      isError: foldersQuery.isError,
    },
    {
      loadingMessage: 'Loading folders',
      showSuccess: false,
      onSuccess: () => {
        const folders = foldersQuery.data?.data?.folders as FolderDetails[];
        dispatch(setFolders(folders));
      },
    },
  );

  // Update Redux store when folders data changes
  useEffect(() => {
    if (foldersQuery.data?.data?.folders) {
      const folders = foldersQuery.data.data.folders as FolderDetails[];
      dispatch(setFolders(folders));

      // Set tagging status to 100% for folders that have taggingCompleted = true
      const completedFolders = folders
        .filter((folder) => folder.taggingCompleted === true)
        .map((folder) => ({
          folder_id: folder.folder_id,
          folder_path: folder.folder_path,
          tagging_percentage: 100,
        }));

      if (completedFolders.length > 0) {
        dispatch(setTaggingStatus(completedFolders));
      }
    }
  }, [foldersQuery.data, dispatch]);

  /* ------------- WebSocket listener for real-time progress updates ------------- */
  useEffect(() => {
    const unsubscribe = addWsListener((msg: any) => {
      // Defensive checks
      if (!msg || typeof msg !== 'object' || !('type' in msg)) return;

      const type = String(msg.type);

      // Handle progress events from backend
      // Message format: { type: 'progress', seq, ts, payload: { job_id, processed, total, percent, status } }
      if (type === 'progress' && msg.payload) {
        try {
          const p = msg.payload as any;
          const jobId = String(p.job_id);
          const percent = Number(p.percent || 0);
          const status = String(p.status || 'running');

          // Check if this job_id corresponds to a folder_id
          // Since backend sends job_id as folder_id for AI tagging operations
          const folder = folders.find((f) => f.folder_id === jobId);

          if (folder) {
            // Convert progress event to FolderTaggingInfo format
            const taggingInfo: FolderTaggingInfo = {
              folder_id: jobId,
              folder_path: folder.folder_path,
              tagging_percentage: Math.round(percent),
            };

            // Update tagging status in Redux
            dispatch(setTaggingStatus([taggingInfo]));

            // If status is 'done', mark tagging as completed (100%)
            if (status === 'done') {
              console.log(`[WS] AI tagging completed for folder: ${jobId}`);
              // Ensure it's set to exactly 100%
              dispatch(
                setTaggingStatus([{ ...taggingInfo, tagging_percentage: 100 }]),
              );
            }
          }
        } catch (e) {
          console.error('[WS] Failed to process progress message', e);
        }
      }
    });

    // Cleanup listener on unmount
    return () => {
      try {
        unsubscribe();
      } catch (e) {
        console.error('[WS] Error unsubscribing', e);
      }
    };
  }, [dispatch, folders]);

  // Enable AI tagging mutation
  const enableAITaggingMutation = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      enableAITagging({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });

  // Apply feedback to the enable AI tagging mutation
  useMutationFeedback(enableAITaggingMutation, {
    showLoading: true,
    loadingMessage: 'Enabling AI tagging',
    successTitle: 'AI Tagging Enabled',
    successMessage: 'AI tagging has been enabled for the selected folder.',
    errorTitle: 'AI Tagging Error',
    errorMessage: 'Failed to enable AI tagging. Please try again.',
  });

  // Disable AI tagging mutation
  const disableAITaggingMutation = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      disableAITagging({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });

  // Apply feedback to the disable AI tagging mutation
  useMutationFeedback(disableAITaggingMutation, {
    showLoading: true,
    loadingMessage: 'Disabling AI tagging',
    successTitle: 'AI Tagging Disabled',
    successMessage: 'AI tagging has been disabled for the selected folder.',
    errorTitle: 'AI Tagging Error',
    errorMessage: 'Failed to disable AI tagging. Please try again.',
  });

  // Delete folder mutation
  const deleteFolderMutation = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      deleteFolders({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });

  // Apply feedback to the delete folder mutation
  useMutationFeedback(deleteFolderMutation, {
    showLoading: true,
    loadingMessage: 'Deleting folder',
    successTitle: 'Folder Deleted',
    successMessage:
      'The folder has been successfully removed from your library.',
    errorTitle: 'Delete Error',
    errorMessage: 'Failed to delete the folder. Please try again.',
  });

  /**
   * Toggle AI tagging for a folder
   */
  const toggleAITagging = (folder: FolderDetails) => {
    if (folder.AI_Tagging) {
      disableAITaggingMutation.mutate(folder.folder_id);
    } else {
      enableAITaggingMutation.mutate(folder.folder_id);
    }
  };

  /**
   * Delete a folder
   */
  const deleteFolder = (folderId: string) => {
    deleteFolderMutation.mutate(folderId);
  };

  return {
    // Data
    folders,
    isLoading: foldersQuery.isLoading,

    // Operations
    toggleAITagging,
    deleteFolder,

    // Mutation states (for use in UI, e.g., disabling buttons)
    enableAITaggingPending: enableAITaggingMutation.isPending,
    disableAITaggingPending: disableAITaggingMutation.isPending,
    deleteFolderPending: deleteFolderMutation.isPending,
  };
};

export default useFolderOperations;
