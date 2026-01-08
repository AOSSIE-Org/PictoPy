import React from 'react';
import { Folder, Trash2, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

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

  const [isExpanded, setIsExpanded] = useState(true);

  const taggingStatus = useSelector(
    (state: RootState) => state.folders.taggingStatus,
  );

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
      action={
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      }
    >
      {isExpanded && (
        <div className="animate-in fade-in slide-in-from-top-2 duration-200">
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
                      <div className="text-muted-foreground mb-1 flex items-center justify-between text-xs">
                        <span>AI Tagging Progress</span>
                        <span
                          className={
                            (taggingStatus[folder.folder_id]
                              ?.tagging_percentage ?? 0) >= 100
                              ? 'flex items-center gap-1 text-green-500'
                              : 'text-muted-foreground'
                          }
                        >
                          {(taggingStatus[folder.folder_id]
                            ?.tagging_percentage ?? 0) >= 100 && (
                            <Check className="h-3 w-3" />
                          )}
                          {Math.round(
                            taggingStatus[folder.folder_id]
                              ?.tagging_percentage ?? 0,
                          )}
                          %
                        </span>
                      </div>
                      <Progress
                        value={
                          taggingStatus[folder.folder_id]?.tagging_percentage ??
                          0
                        }
                        indicatorClassName={
                          (taggingStatus[folder.folder_id]
                            ?.tagging_percentage ?? 0) >= 100
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
        </div>
      )}
    </SettingsCard>
  );
};

export default FolderManagementCard;
