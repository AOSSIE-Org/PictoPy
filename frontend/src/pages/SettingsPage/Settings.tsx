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
      <div className="space-y-6 rounded-3xl bg-theme-light dark:bg-theme-dark p-6 shadow">
        <div>
          <h2 className="mb-2 text-lg font-medium text-theme-dark dark:text-theme-light">
            Current Folder Path
          </h2>
          <div className="rounded-md bg-gray-100 dark:bg-gray-800 px-4 py-3 text-theme-dark dark:text-theme-light">
            {currentPath && <>{currentPath}</>}
          </div>
        </div>
        <FolderPicker setFolderPath={handleFolderPathChange} />
        <Button
          onClick={handleDeleteCache}
          variant="outline"
          className="border-gray-500 text-theme-dark dark:text-theme-light hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <RefreshCwIcon className="mr-2 h-5 w-5 text-theme-dark dark:text-theme-light" />
          Refresh Cache
        </Button>
      </div>
    </div>
  );
};

export default Settings;
