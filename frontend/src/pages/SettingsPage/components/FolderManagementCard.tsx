import React, { useState } from 'react';
import { Folder, Trash2, Check } from 'lucide-react';

import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSelector } from 'react-redux';
import { RootState } from '@/store/store';
// import { RootState } from '@/app/store';
import FolderPicker from '@/components/FolderPicker/FolderPicker';

import { useFolderOperations } from '@/hooks/useFolderOperations';
import { FolderDetails } from '@/types/Folder';
import SettingsCard from './SettingsCard';

/**
 * Component for managing folder operations in settings
 */
const FolderManagementCard: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  // const [selectedFolder, setSelectedFolder] = useState<any>(null);
  // const taggingStatus = useSelector((state: any) => state.folders.taggingStatus || {});
  const {
    folders,
    toggleAITagging,
    deleteFolder,
    enableAITaggingPending,
    disableAITaggingPending,
    deleteFolderPending,
  } = useFolderOperations();

  const taggingStatus = useSelector(
    (state: RootState) => state.folders.taggingStatus,
  );

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {folders.length > 0 ? (
        <div className="space-y-3">
          {folders.map((folder: FolderDetails, index: number) => (
            <div
              key={index}
              className="group border-border bg-background/50 relative rounded-lg border p-4 transition-all hover:border-gray-300 hover:shadow-sm dark:hover:border-gray-600"
            >
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <Folder className="h-4 w-4 flex-shrink-0 text-gray-500 dark:text-gray-400" />
                    <span className="text-foreground truncate">
                      {folder.folder_path}
                    </span>
                  </div>
                </div>

                <div className="ml-4 flex items-center gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-muted-foreground text-sm">
                      AI Tagging
                    </span>
                    <Switch
                      className="cursor-pointer"
                      checked={folder.AI_Tagging}
                      onCheckedChange={() => toggleAITagging(folder)}
                      disabled={
                        enableAITaggingPending || disableAITaggingPending
                      }
                    />
                  </div>

                  <Button
                    // onClick={() => deleteFolder(folder.folder_id)}
                    onClick={() => {
                      setSelectedFolder(folder.folder_id);
                      setIsModalOpen(true);
                    }}
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 cursor-pointer text-gray-500 hover:border-red-300 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                    disabled={deleteFolderPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {folder.AI_Tagging && (
                <div className="mt-3">
                  <div className="text-muted-foreground mb-1 flex items-center justify-between text-xs">
                    <span>AI Tagging Progress</span>
                    <span
                      className={
                        (taggingStatus[folder.folder_id]?.tagging_percentage ??
                          0) >= 100
                          ? 'flex items-center gap-1 text-green-500'
                          : 'text-muted-foreground'
                      }
                    >
                      {(taggingStatus[folder.folder_id]?.tagging_percentage ??
                        0) >= 100 && <Check className="h-3 w-3" />}
                      {Math.round(
                        taggingStatus[folder.folder_id]?.tagging_percentage ??
                          0,
                      )}
                      %
                    </span>
                  </div>
                  <Progress
                    value={
                      taggingStatus[folder.folder_id]?.tagging_percentage ?? 0
                    }
                    indicatorClassName={
                      (taggingStatus[folder.folder_id]?.tagging_percentage ??
                        0) >= 100
                        ? 'bg-green-500'
                        : 'bg-blue-500'
                    }
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center">
          <Folder className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <h3 className="text-foreground mb-1 text-lg font-medium">
            No folders configured
          </h3>
          <p className="text-muted-foreground text-sm">
            Add your first photo library folder to get started
          </p>
        </div>
      )}

      <div className="border-border mt-6 border-t pt-6">
        <FolderPicker />
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-6 shadow-2xl dark:border-gray-800 dark:bg-gray-900">
            <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
              Delete Folder?
            </h3>
            <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
              Are you sure? This will remove the folder from the library but not
              from your computer.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (selectedFolder) deleteFolder(selectedFolder);
                  setIsModalOpen(false);
                }}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </SettingsCard>
  );
};

export default FolderManagementCard;
