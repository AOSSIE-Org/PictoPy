import { useCallback } from 'react';
import { open } from '@tauri-apps/plugin-dialog';
import { usePictoMutation } from './useQueryExtension';
import { useMutationFeedback } from './useMutationFeedback';
import { addFolder } from '@/api/api-functions';

interface UseFolderPickerOptions {
  title?: string;
}

interface UseFolderPickerReturn {
  pickSingleFolder: () => Promise<string | null>;
  addFolderMutate: (folderPath: string) => void;
}

export const useFolder = (
  options: UseFolderPickerOptions = {},
): UseFolderPickerReturn => {
  const { title = 'Select folder' } = options;

  const {
    mutate: addFolderMutate,
    isSuccess: addFolderSuccess,
    isError: addFolderError,
    isPending: addFolderPending,
    error,
  } = usePictoMutation({
    mutationFn: async (folder_path: string) => addFolder({ folder_path }),
    autoInvalidateTags: ['folders'],
  });

  useMutationFeedback(
    {
      isPending: addFolderPending,
      isSuccess: addFolderSuccess,
      isError: addFolderError,
      error,
    },
    {
      successTitle: 'Folder Added',
      successMessage: 'The folder has been successfully added.',
      errorTitle: 'Error',
    },
  );

  const pickSingleFolder = useCallback(async (): Promise<string | null> => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title,
      });

      if (selected && typeof selected === 'string') {
        return selected;
      }

      return null;
    } catch (error) {
      console.error('Error picking folder:', error);
      return null;
    }
  }, [title]);

  return {
    addFolderMutate,
    pickSingleFolder,
  };
};
