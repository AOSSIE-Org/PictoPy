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
import { getFoldersTaggingStatus } from '@/api/api-functions/folders';

/**
 * Custom hook for folder operations
 * Manages folder queries, AI tagging mutations, and folder deletion
 */
export const useFolderOperations = () => {
  const dispatch = useDispatch();
  const folders = useSelector(selectAllFolders);

  // Query for folders
  const foldersQuery = usePictoQuery({
    queryKey: ['folders'],
    queryFn: getAllFolders,
  });

  const taggingStatusQuery = usePictoQuery({
    queryKey: ['folders', 'tagging-status'],
    queryFn: getFoldersTaggingStatus,
    staleTime: 1000,
    refetchInterval: 1000,
    refetchIntervalInBackground: true,
    enabled: folders.some((f) => f.AI_Tagging),
    retry: 2, // Retry failed requests up to 2 times before giving up
    retryOnMount: false, // Don't retry on component mount
    refetchOnWindowFocus: false, // Don't refetch when window gains focus
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
    }
  }, [foldersQuery.data, dispatch]);

  // Update Redux store with tagging status on each poll
  useEffect(() => {
    if (taggingStatusQuery.data?.success) {
      const raw = taggingStatusQuery.data.data as any;
      if (Array.isArray(raw)) {
        dispatch(setTaggingStatus(raw));
      }
    }
  }, [taggingStatusQuery.data, dispatch]);

  useEffect(() => {
    if (taggingStatusQuery.isError) {
      console.error(
        'Failed to fetch tagging status:',
        taggingStatusQuery.error,
      );

      const errorMessage = taggingStatusQuery.errorMessage || 'Unknown error';
      console.warn(`Tagging status query failed: ${errorMessage}`);
    }
  }, [
    taggingStatusQuery.isError,
    taggingStatusQuery.error,
    taggingStatusQuery.errorMessage,
  ]);

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
    showSuccess: false,
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
