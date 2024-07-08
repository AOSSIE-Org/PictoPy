import React from "react";
import FolderPicker from "@/components/FolderPicker/FolderPicker";

import { deleteCache } from "@/services/cacheService";
import { Button } from "@/components/ui/button";
import { RefreshCwIcon } from "@/components/Icons/Icons";
import { useLocalStorage } from "@/hooks/LocalStorage";

const Settings: React.FC = () => {
  const [currentPath, setCurrentPath] = useLocalStorage("folderPath", "abc");

  const handleFolderPathChange = (newPath: string) => {
    setCurrentPath(newPath);
  };

  const handleDeleteCache = async () => {
    try {
      const result = await deleteCache();
      if (result) {
        console.log("Cache deleted");
      }
    } catch (error) {
      console.error("Error deleting cache:", error);
    }
  };

  return (
    <div className="flex-1 container mx-auto px-4 py-8">
      <div className="bg-gray-800 dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
        <div>
          <h2 className="text-lg font-medium text-gray-50 dark:text-gray-50 mb-2">
            Current Folder Path
          </h2>
          <div className="bg-gray-700 dark:bg-gray-700 rounded-md px-4 py-3 text-gray-300 dark:text-gray-300">
            {currentPath && <>{currentPath}</>}
          </div>
        </div>
        <FolderPicker setFolderPath={handleFolderPathChange} />
        <Button
          onClick={handleDeleteCache}
          variant="outline"
          className="text-gray-50 dark:text-gray-50 border-gray-500 dark:border-gray-500 hover:bg-gray-700 dark:hover:bg-gray-700"
        >
          <RefreshCwIcon className="mr-2 h-5 w-5 text-gray-50 dark:text-gray-50" />
          Refresh Cache
        </Button>
      </div>
    </div>
  );
};

export default Settings;
