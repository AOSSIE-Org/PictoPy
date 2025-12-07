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
import {
  DEFAULT_RETRY_COUNT,
  TAGGING_STATUS_POLL_INTERVAL,
} from '@/config/pagination';

export const useFolderOperations = () => {
  const dispatch = useDispatch();
  const folders = useSelector(selectAllFolders);

  const foldersQuery = usePictoQuery({
    queryKey: ['folders'],
    queryFn: getAllFolders,
  });

  const taggingStatusQuery = usePictoQuery({
    queryKey: ['folders', 'tagging-status'],
    queryFn: getFoldersTaggingStatus,
    staleTime: TAGGING_STATUS_POLL_INTERVAL,
    refetchInterval: TAGGING_STATUS_POLL_INTERVAL,
    refetchIntervalInBackground: true,
    enabled: folders.some((f) => f.AI_Tagging),
    retry: DEFAULT_RETRY_COUNT,
    retryOnMount: false,
    refetchOnWindowFocus: false,
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
    autoInvalidateTags: ['folders', 'images'],
    onMutate: async (folder_id: string) => {
      const previousFolders = [...folders];
      const updatedFolders = folders.map(f => 
        f.folder_id === folder_id ? { ...f, AI_Tagging: true } : f
      );
      dispatch(setFolders(updatedFolders));
      return { previousFolders };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousFolders) {
        dispatch(setFolders(context.previousFolders));
      }
    },
  });

  useMutationFeedback(enableAITaggingMutation, {
    showLoading: true,
    loadingMessage: 'Enabling AI tagging',
    successTitle: 'AI Tagging Enabled',
    successMessage: 'AI tagging has been enabled for the selected folder.',
    errorTitle: 'AI Tagging Error',
    errorMessage: 'Failed to enable AI tagging. Please try again.',
  });

  const disableAITaggingMutation = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      disableAITagging({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders', 'images'],
    onMutate: async (folder_id: string) => {
      const previousFolders = [...folders];
      const updatedFolders = folders.map(f => 
        f.folder_id === folder_id ? { ...f, AI_Tagging: false } : f
      );
      dispatch(setFolders(updatedFolders));
      return { previousFolders };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousFolders) {
        dispatch(setFolders(context.previousFolders));
      }
    },
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
    autoInvalidateTags: ['folders', 'images'],
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
    folders,
    isLoading: foldersQuery.isLoading,
    toggleAITagging,
    deleteFolder,
    enableAITaggingPending: enableAITaggingMutation.isPending,
    disableAITaggingPending: disableAITaggingMutation.isPending,
    deleteFolderPending: deleteFolderMutation.isPending,
  };
};

export default useFolderOperations;
