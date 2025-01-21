import React from 'react';
import FolderPicker from '@/components/FolderPicker/FolderPicker';
import { useState } from 'react';
import { deleteCache } from '@/services/cacheService';
import { Button } from '@/components/ui/button';
import { FolderSync, Server } from 'lucide-react';
import { useLocalStorage } from '@/hooks/LocalStorage';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
import { restartServer } from '@/utils/serverUtils';
import { isProd } from '@/utils/isProd';
const Settings: React.FC = () => {
  const [currentPath, setCurrentPath] = useLocalStorage('folderPath', '');
  const [isLoading, setIsLoading] = useState(false);
  const handleFolderPathChange = async (newPath: string) => {
    setCurrentPath(newPath);
    await deleteCache();
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

  if (isLoading) {
    return (
      <div>
        <LoadingScreen />
      </div>
    );
  }

  return (
    <div className="mx-auto flex-1 px-4 pt-1">
      <div className="bg-theme-light rounded-2xl space-y-6 border border-white/10 p-6 shadow backdrop-blur-md backdrop-saturate-150 dark:border-white/5 dark:bg-white/5">
        <div>
          <h2 className="text-theme-dark dark:text-theme-light mb-2 text-lg font-medium">
            Current Folder Path
          </h2>
          <div className="text-theme-dark dark:text-theme-light rounded-md border bg-gray-100 px-4 py-3 backdrop-blur-sm dark:border-white/5 dark:bg-white/5">
            {currentPath && <>{currentPath}</>}
          </div>
        </div>
        <div className="w-40 space-y-4">
          <FolderPicker
            setFolderPath={handleFolderPathChange}
            className="h-10 w-full"
            settingsPage={true}
            setIsLoading={setIsLoading}
            handleDeleteCache={handleDeleteCache}
          />
          <Button
            onClick={handleDeleteCache}
            variant="outline"
            className="h-10 w-full border-gray-500 hover:bg-accent dark:hover:bg-white/10"
          >
            <FolderSync className="text-gray-5 mr-2 h-5 w-5 dark:text-gray-50" />
            Refresh Cache
          </Button>
          {isProd() && (
            <Button
              onClick={() => restartServer(setIsLoading)}
              variant="outline"
              className="h-10 w-full border-gray-500 hover:bg-accent dark:hover:bg-white/10"
            >
              <Server className="text-gray-5 mr-2 h-5 w-5 dark:text-gray-50" />
              Restart Server
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
