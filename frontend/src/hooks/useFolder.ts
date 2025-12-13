import { useCallback, useEffect } from 'react';
import { open } from '@tauri-apps/plugin-dialog';
import { usePictoMutation } from './useQueryExtension';
import { addFolder } from '@/api/api-functions';
import { useQueryClient } from '@tanstack/react-query';

interface UseFolderPickerOptions {
  title?: string;
}

interface UseFolderPickerReturn {
  pickSingleFolder: () => Promise<string | null>;
  addFolderMutate: (folderPath: string) => void;
  isAddingFolder: boolean;
}

//polling refs outside component to persist across remounts
const pollIntervalRef: { current: NodeJS.Timeout | null } = { current: null };
const previousImageCountRef: { current: number } = { current: 0 };
const stableCountIterationsRef: { current: number } = { current: 0 };

export const useFolder = (
  options: UseFolderPickerOptions = {},
): UseFolderPickerReturn => {
  const { title = 'Select folder' } = options;
  const queryClient = useQueryClient();

  const {
    mutate: addFolderMutate,
    isSuccess: addFolderSuccess,
    isError: addFolderError,
    isPending: addFolderPending,
  } = usePictoMutation({
    mutationFn: async (folder_path: string) => addFolder({ folder_path }),
    autoInvalidateTags: ['folders'],
    onSuccess: () => {
     // console.log('onSuccess called - starting polling setup');
      // Reset Counters
      previousImageCountRef.current = 0;
      stableCountIterationsRef.current = 0;

      // Immediately invalidate images to show first batch
      queryClient.invalidateQueries({ queryKey: ['images'] });

      // Clear any existing polling interval
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
       // console.log('Cleared existing interval');
      }
      // Start polling for incremental updates every 2 seconds;
      pollIntervalRef.current = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['images'] });
        // Get current image count
        const imagesData = queryClient.getQueryData(['images']) as any;
        const currentImageCount = imagesData?.data?.length || 0;
        // Check if count has stabilized
        if (currentImageCount === previousImageCountRef.current && currentImageCount > 0) {
          stableCountIterationsRef.current += 1;
          
          if (stableCountIterationsRef.current >= 3) {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
              //console.log('✓ Processing complete! Total images:', currentImageCount);
            }
          }
        } else {
          // Count changed, reset stability counter
          stableCountIterationsRef.current = 0;
          previousImageCountRef.current = currentImageCount;
          //console.log('Image count changed to:', currentImageCount);
        }
      }, 2000); // Poll every 2 seconds
    },
  });

  useEffect(() => {
    if (addFolderPending) {
      console.log('Adding folder...');
    } else if (addFolderSuccess) {
      console.log('Folder added successfully - starting to poll for images');
    } else if (addFolderError) {
      console.error('Error adding folder');
      // Clear polling on error
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [addFolderSuccess, addFolderError, addFolderPending]);

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
    isAddingFolder: addFolderPending,
  };
};