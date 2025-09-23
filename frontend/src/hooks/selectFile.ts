import { open } from '@tauri-apps/plugin-dialog';
import { useCallback } from 'react';
interface UseFolderPickerOptions {
  title?: string;
}

interface UseFilePickerReturn {
  pickSingleFile: () => Promise<string | null>;
}

export const useFile = (
  options: UseFolderPickerOptions = {},
): UseFilePickerReturn => {
  const { title = 'Select File' } = options;
  const pickSingleFile = useCallback(async (): Promise<(
    string) | null> => {
    try {
      const selected = await open({
        multiple: false,
        filters: [
          {
            name: 'Images',
            extensions: ['png', 'jpg', 'jpeg', 'gif', 'bmp'],
          },
        ],
        title,
      });

      if (selected && typeof selected === 'string') {
        return selected
      }
      return null;
    } catch (error) {
      console.error('Error picking File:', error);
      return null;
    }
  }, [title]);

  return { pickSingleFile} ;
};
