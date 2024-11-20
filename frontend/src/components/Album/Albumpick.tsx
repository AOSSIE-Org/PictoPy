import React from 'react';
import { Button } from '../ui/button';

import { open } from '@tauri-apps/plugin-dialog';
import { FileIcon } from '../ui/Icons/Icons';

interface FilePickerProps {
  setFilePaths: (paths: string[]) => void;
  multiple?: boolean;
}

const FilePicker: React.FC<FilePickerProps> = ({
  setFilePaths,
  multiple = true,
}) => {
  const pickFiles = async () => {
    try {
      const selected = await open({
        multiple,
        filters: [
          {
            name: 'Image',
            extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp'],
          },
        ],
      });
      if (selected) {
        if (Array.isArray(selected)) {
          setFilePaths(selected);
        } else if (typeof selected === 'string') {
          setFilePaths([selected]);
        }
      }
    } catch (error) {
      console.error('Error picking files:', error);
    }
  };

  return (
    <div className="flex gap-3">
      <Button
        onClick={pickFiles}
        variant="outline"
        className="text-black-50 border-gray-500 hover:bg-gray-700 dark:border-gray-500 dark:text-gray-50 dark:hover:bg-gray-700"
      >
        <FileIcon className="text-black-50 mr-2 h-5 w-5 dark:text-gray-50" />
        Choose {multiple ? 'Files' : 'File'}
      </Button>
    </div>
  );
};

export default FilePicker;
