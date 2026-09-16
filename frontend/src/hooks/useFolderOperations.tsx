import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useQueryClient } from '@tanstack/react-query';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import {
  enableAITagging,
  getAllFolders,
  disableAITagging,
  deleteFolders,
} from '@/api/api-functions';
import { selectAllFolders } from '@/features/folderSelectors';
import { setFolders, setTaggingStatus } from '@/features/folderSlice';
import { FolderDetails, isIndexingPending } from '@/types/Folder';
import { useMutationFeedback } from './useMutationFeedback';
import { getFoldersTaggingStatus } from '@/api/api-functions/folders';

export const useFolderOperations = () => {
  const dispatch = useDispatch();
  const queryClient = useQueryClient();
  const folders = useSelector(selectAllFolders);

  const foldersQuery = usePictoQuery({
    queryKey: ['folders'],
    queryFn: getAllFolders,
    refetchInterval: folders.some(
      (f) => f.AI_Tagging && isIndexingPending(f.indexing_status),
    )
      ? 1000
      : false,
    refetchIntervalInBackground: true,
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

  useEffect(() => {
    if (foldersQuery.data?.data?.folders) {
      const folders = foldersQuery.data.data.folders as FolderDetails[];
      dispatch(setFolders(folders));
    }
  }, [foldersQuery.data, dispatch]);

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

  const enableAITaggingMutation = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      enableAITagging({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });

  useMutationFeedback(enableAITaggingMutation, {
    showLoading: true,
    loadingMessage: 'Enabling AI tagging',
    showSuccess: false,
    errorTitle: 'AI Tagging Error',
    errorMessage: 'Failed to enable AI tagging. Please try again.',
  });

  const disableAITaggingMutation = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      disableAITagging({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });

  useMutationFeedback(disableAITaggingMutation, {
    showLoading: true,
    loadingMessage: 'Disabling AI tagging',
    successTitle: 'AI Tagging Disabled',
    successMessage: 'AI tagging has been disabled for the selected folder.',
    errorTitle: 'AI Tagging Error',
    errorMessage: 'Failed to disable AI tagging. Please try again.',
  });

  const deleteFolderMutation = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      deleteFolders({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
    // Deleting a folder cascades to its images and faces, so clusters go stale.
    // Separate call: autoInvalidateTags is one prefix-matched key, not a list.
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] });
    },
  });

  useMutationFeedback(deleteFolderMutation, {
    showLoading: true,
    loadingMessage: 'Deleting folder',
    successTitle: 'Folder Deleted',
    successMessage:
      'The folder has been successfully removed from your library.',
    errorTitle: 'Delete Error',
    errorMessage: 'Failed to delete the folder. Please try again.',
  });

  const toggleAITagging = (folder: FolderDetails) => {
    if (folder.AI_Tagging) {
      disableAITaggingMutation.mutate(folder.folder_id);
    } else {
      enableAITaggingMutation.mutate(folder.folder_id);
    }
  };

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
