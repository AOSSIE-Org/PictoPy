import React, { useState } from 'react';
import FolderPicker from '@/components/FolderPicker/FolderPicker';
import { deleteCache } from '@/services/cacheService';
import { Button } from '@/components/ui/button';
import { FolderSync, Server, Edit, Save, X, Loader2 } from 'lucide-react';
import { useLocalStorage } from '@/hooks/LocalStorage';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
import { restartServer } from '@/utils/serverUtils';
import { isProd } from '@/utils/isProd';

const Settings: React.FC = () => {
  const [currentPath, setCurrentPath] = useLocalStorage('folderPath', '');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [tempPath, setTempPath] = useState(currentPath);
  const [isRefreshing, setIsRefreshing] = useState(false); // For refresh cache loading

  const handleFolderPathChange = async (newPath: string) => {
    setCurrentPath(newPath);
    await deleteCache();
  };

  const handleDeleteCache = async () => {
    try {
      setIsRefreshing(true);
      await deleteCache();
      setTimeout(() => setIsRefreshing(false), 1000); // Simulate refresh delay
    } catch (error) {
      console.error('Error deleting cache:', error);
      setIsRefreshing(false);
    }
  };

  const handleEditClick = () => setIsEditing(true);
  const handleSaveClick = () => {
    setCurrentPath(tempPath);
    setIsEditing(false);
    handleDeleteCache();
  };
  const handleCancelClick = () => {
    setTempPath(currentPath);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSaveClick();
    else if (e.key === 'Escape') handleCancelClick();
  };

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="mx-auto flex-1 px-4 pt-1">
      <div className="bg-theme-light rounded-2xl space-y-6 border border-white/10 p-6 shadow backdrop-blur-md backdrop-saturate-150 dark:border-white/5 dark:bg-white/5">
        <div>
          <h2 className="text-theme-dark dark:text-theme-light mb-2 text-lg font-medium">
            Current Folder Path
          </h2>
          <div className="flex items-center space-x-2 rounded-md border bg-gray-100 px-4 py-3 backdrop-blur-sm dark:border-white/5 dark:bg-white/5">
            {isEditing ? (
              <input
                type="text"
                value={tempPath}
                onChange={(e) => setTempPath(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 bg-transparent p-1 border-none outline-none text-theme-dark dark:text-theme-light"
              />
            ) : (
              <span className="flex-1 text-theme-dark dark:text-theme-light">
                {currentPath || 'No folder selected'}
              </span>
            )}
            {isEditing ? (
              <>
                <Button onClick={handleSaveClick} size="icon" variant="ghost">
                  <Save className="w-5 h-5 text-green-500" />
                </Button>
                <Button onClick={handleCancelClick} size="icon" variant="ghost">
                  <X className="w-5 h-5 text-red-500" />
                </Button>
              </>
            ) : (
              <Button onClick={handleEditClick} size="icon" variant="ghost">
                <Edit className="w-5 h-5 text-gray-500" />
              </Button>
            )}
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
            disabled={isRefreshing} // Disable while loading
          >
            {isRefreshing ? (
              <Loader2 className="animate-spin text-gray-500 mr-2 h-5 w-5 dark:text-gray-50" />
            ) : (
              <FolderSync className="text-gray-500 mr-2 h-5 w-5 dark:text-gray-50" />
            )}
            {isRefreshing ? 'Refreshing...' : 'Refresh Cache'}
          </Button>
          {isProd() && (
            <Button
              onClick={() => restartServer(setIsLoading)}
              variant="outline"
              className="h-10 w-full border-gray-500 hover:bg-accent dark:hover:bg-white/10"
            >
              <Server className="text-gray-500 mr-2 h-5 w-5 dark:text-gray-50" />
              Restart Server
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
