import React from 'react';
import FolderPicker from '@/components/FolderPicker/FolderPicker';

import { deleteCache } from '@/services/cacheService';
import { Button } from '@/components/ui/button';
import { FolderSync } from 'lucide-react';
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
    <div className="mx-auto flex-1 px-4 pt-1">
      <div className="space-y-6 rounded-2xl border border-white/10 bg-white/5 p-6 shadow backdrop-blur-md backdrop-saturate-150 dark:border-white/5">
        <div>
          <h2 className="mb-2 text-lg font-medium text-gray-50 dark:text-gray-50">
            Current Folder Path
          </h2>
          <div className="rounded-md border border-white/5 bg-white/5 px-4 py-3 text-gray-300 backdrop-blur-sm dark:text-gray-300">
            {currentPath && <>{currentPath}</>}
          </div>
        </div>
        <div className="w-40 space-y-4">
          <FolderPicker
            setFolderPath={handleFolderPathChange}
            className="h-10 w-full"
            settingsPage={true}
          />
          <Button
            onClick={handleDeleteCache}
            variant="outline"
            className="h-10 w-full border-white text-gray-50 hover:bg-white dark:text-gray-50"
          >
            <FolderSync className="text-gray-5 mr-2 h-5 w-5 dark:text-gray-50" />
            Refresh Cache
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
