import { fetchSearchedFaces } from '@/api/api-functions';
import { APIResponse } from '@/types/API';
import { Image } from '@/types/Media';
import { open } from '@tauri-apps/plugin-dialog';
import { useCallback } from 'react';
interface UseFolderPickerOptions {
  title?: string;
}

interface UseFilePickerReturn {
  pickSingleFile: () => Promise<{
    path: string;
    result: APIResponse;
  } | null>;
}

export const useFile = (
  options: UseFolderPickerOptions = {},
): UseFilePickerReturn => {
  const { title = 'Select File' } = options;
  const pickSingleFile = useCallback(async (): Promise<{
    path: string;
    result: APIResponse;
  } | null> => {
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
        const res: APIResponse = await fetchSearchedFaces({
          path: selected,
        } as Image);
        console.log(res)
        return { path: selected, result: res };
      }
      return null;
    } catch (error) {
      console.error('Error picking File:', error);
      return null;
    }
  }, [title]);

  return { pickSingleFile };
};
