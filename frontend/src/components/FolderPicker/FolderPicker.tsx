import React from 'react';
import { Button } from '../ui/button';
import { open } from '@tauri-apps/plugin-dialog';
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
    try {
      const selected = await open({
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
        className={`flex items-center justify-center border-gray-500 text-gray-700 hover:bg-accent dark:text-gray-50 dark:hover:bg-white/10 ${className} `}
      >
        <FolderPlus className="h-[18px] w-[18px]" />
        <p className={`ml-2 inline`}>Add folders</p>
      </Button>
    </div>
  );
};

export default FolderPicker;
