import React from 'react';
import { Button } from '../ui/button';
import { open } from '@tauri-apps/plugin-dialog';
import { FolderPlus } from 'lucide-react';
import { generateThumbnails } from '../../../api/api-functions/images';
import { usePictoMutation } from '@/hooks/useQueryExtensio';
interface FolderPickerProps {
  setFolderPath: (path: string) => void;
  className?: string;
  settingsPage?: boolean;
  setIsLoading?: (loading: boolean) => void;
  handleDeleteCache?: () => void;
}

const FolderPicker: React.FC<FolderPickerProps> = ({
  setFolderPath,
  className,
  settingsPage,
  setIsLoading,
  handleDeleteCache,
}) => {
  const { mutate: generateThumbnail } = usePictoMutation({
    mutationFn: generateThumbnails,
    onSuccess: () => {
      if (setIsLoading) {
        setIsLoading(false);
      }
    },
    autoInvalidateTags: ['ai-tagging-images', 'ai'],
  });

  const pickFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Select a folder',
      });
      if (selected && typeof selected === 'string') {
        setFolderPath(selected);
        console.log('Selected folder:', selected);
        if (settingsPage) {
          setIsLoading && setIsLoading(true);
          generateThumbnail(selected);
        }
        if (handleDeleteCache) {
          handleDeleteCache();
        }
      }
    } catch (error) {
      console.error('Error picking folder:', error);
    }
  };
  return (
    <div className="flex w-full gap-3">
      <Button
        onClick={pickFolder}
        variant="outline"
        className={`flex items-center justify-center border-gray-500 text-gray-700 hover:bg-accent dark:text-gray-50 dark:hover:bg-white/10 ${className} `}
      >
        <FolderPlus className="h-[18px] w-[18px]" />
        <p className={`ml-2 ${!settingsPage && 'hidden lg:inline'}`}>
          Add folder
        </p>
      </Button>
    </div>
  );
};

export default FolderPicker;
