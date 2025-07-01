import React from 'react';
import { Button } from '@/components/ui/button';
import { safeTauriDialogOpen, isTauriEnvironment } from '@/utils/tauriUtils';
import { FolderPlus } from 'lucide-react';

interface FolderPickerProps {
  setFolderPaths: (paths: string[]) => void;
  className?: string;
}

const FolderPicker: React.FC<FolderPickerProps> = ({
  setFolderPaths,
  className,
}) => {
  const pickFolder = async () => {
    if (!isTauriEnvironment()) {
      alert('Folder selection is only available in desktop mode. Please run the app using "npm run tauri dev" instead of "npm run dev".');
      return;
    }

    try {
      const selected = await safeTauriDialogOpen({
        directory: true,
        multiple: true, // Allow multiple folder selection
        title: 'Select folders',
      });
      if (selected && Array.isArray(selected)) {
        setFolderPaths(selected);
      }
    } catch (error) {
      console.error('Error picking folders:', error);
    }
  };

  return (
    <div className="flex w-full gap-3">
      <Button
        onClick={pickFolder}
        variant="outline"
        className={`hover:bg-accent flex items-center justify-center border-gray-500 text-gray-700 dark:text-gray-50 dark:hover:bg-white/10 ${className} `}
      >
        <FolderPlus className="h-[18px] w-[18px]" />
        <p className={`ml-2 inline`}>Add folders</p>
      </Button>
    </div>
  );
};

export default FolderPicker;
