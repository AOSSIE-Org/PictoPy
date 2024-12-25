import React from 'react';
import { Button } from '../ui/button';
import { open } from '@tauri-apps/plugin-dialog';
import { FolderOpenIcon } from '../ui/Icons/Icons';

interface FolderPickerProps {
  setFolderPath: (path: string) => void;
}

const FolderPicker: React.FC<FolderPickerProps> = ({ setFolderPath }) => {
  const pickFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Select a folder',
      });
      if (selected && typeof selected === 'string') {
        setFolderPath(selected);
      }
    } catch (error) {
      console.error('Error picking folder:', error);
    }
  };

  return (
    <div className="flex gap-3">
      <Button
        onClick={pickFolder}
        variant="outline"
        className="border-gray-500 text-theme-dark dark:text-theme-light hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        <FolderOpenIcon className="mr-2 h-5 w-5 text-theme-dark dark:text-theme-light" />
        Add folder
      </Button>
    </div>
  );
};

export default FolderPicker;
