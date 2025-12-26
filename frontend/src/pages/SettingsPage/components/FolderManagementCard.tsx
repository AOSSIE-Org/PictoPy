import React from 'react';
import { Folder, Trash2, Check, Loader2, AlertCircle } from 'lucide-react';

import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import FolderPicker from '@/components/FolderPicker/FolderPicker';

import { useFolderOperations } from '@/hooks/useFolderOperations';
import { FolderDetails } from '@/types/Folder';
import SettingsCard from './SettingsCard';

/**
 * Component for managing folder operations in settings
 */
const FolderManagementCard: React.FC = () => {
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
  const folderStatusTimestamps = useSelector(
    (state: RootState) => state.folders.folderStatusTimestamps,
  );

  const isStatusLoading = (folderId: string, folderHasAITagging: boolean) => {
    if (!folderHasAITagging) return false;

    const status = taggingStatus[folderId];
    if (!status) return true;

    const timestamp = folderStatusTimestamps[folderId];
    if (!timestamp) return true;

    const timeSinceUpdate = Date.now() - timestamp;

    if (status.total_images === 0 && timeSinceUpdate < 3000) {
      return true;
    }

    return false;
  };

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {folders.length > 0 ? (
        <div className="space-y-3">
          {folders.map((folder: FolderDetails, index: number) => {
            const status = taggingStatus[folder.folder_id];
            const loading = isStatusLoading(
              folder.folder_id,
              folder.AI_Tagging,
            );
            const hasImages = status && status.total_images > 0;
            const isEmpty = status && status.total_images === 0 && !loading;
            const isComplete = status && status.tagging_percentage >= 100;

            return (
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
                      onClick={() => deleteFolder(folder.folder_id)}
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
                    {loading ? (
                      <div className="text-muted-foreground flex items-center gap-2 text-xs">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        <span>Loading status...</span>
                      </div>
                    ) : isEmpty ? (
                      <div className="text-muted-foreground flex items-center gap-2 text-xs">
                        <AlertCircle className="h-3 w-3" />
                        <span>No images found in this folder</span>
                      </div>
                    ) : hasImages ? (
                      <>
                        <div className="text-muted-foreground mb-1 flex items-center justify-between text-xs">
                          <span>AI Tagging Progress</span>
                          <span
                            className={
                              isComplete
                                ? 'flex items-center gap-1 text-green-500'
                                : 'text-muted-foreground'
                            }
                          >
                            {isComplete && <Check className="h-3 w-3" />}
                            {Math.round(status.tagging_percentage)}%
                          </span>
                        </div>
                        <Progress
                          value={status.tagging_percentage}
                          indicatorClassName={
                            isComplete ? 'bg-green-500' : 'bg-blue-500'
                          }
                        />
                      </>
                    ) : null}
                  </div>
                )}
              </div>
            );
          })}
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
    </SettingsCard>
  );
};

export default FolderManagementCard;
