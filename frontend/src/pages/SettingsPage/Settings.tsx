import React from 'react';
import FolderPicker from '@/components/FolderPicker/FolderPicker';

import { deleteCache } from '@/services/cacheService';
import { Button } from '@/components/ui/button';
import { RefreshCwIcon } from '@/components/ui/Icons/Icons';
import { useLocalStorage } from '@/hooks/LocalStorage';

const Settings: React.FC = () => {
  const [currentPath, setCurrentPath] = useLocalStorage('folderPath', 'abc');

  const handleFolderPathChange = (newPath: string) => {
    setCurrentPath(newPath);
  };

  const handleDeleteCache = async () => {
    try {
      const result = await deleteCache();
      if (result) {
        console.log('Cache deleted');
      }
    } catch (error) {
      console.error('Error deleting cache:', error);
    }
  };

  return (
    <div className="container mx-auto flex-1 px-4 py-8">
      <div className="space-y-6 rounded-lg bg-gray-800 p-6 shadow dark:bg-gray-800">
        <div>
          <h2 className="mb-2 text-lg font-medium text-gray-50 dark:text-gray-50">
            Current Folder Path
          </h2>
          <div className="rounded-md bg-gray-700 px-4 py-3 text-gray-300 dark:bg-gray-700 dark:text-gray-300">
            {currentPath && <>{currentPath}</>}
          </div>
        </div>
        <FolderPicker setFolderPath={handleFolderPathChange} />
        <Button
          onClick={handleDeleteCache}
          variant="outline"
          className="border-gray-500 text-gray-50 hover:bg-gray-700 dark:border-gray-500 dark:text-gray-50 dark:hover:bg-gray-700"
        >
          <RefreshCwIcon className="mr-2 h-5 w-5 text-gray-50 dark:text-gray-50" />
          Refresh Cache
        </Button>
      </div>
    </div>
  );
};

export default Settings;
