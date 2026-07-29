import React, { useState } from 'react';
import { AlertTriangle, Folder, Trash2, Check, Loader2 } from 'lucide-react';

import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import FolderPicker from '@/components/FolderPicker/FolderPicker';

import { Badge } from '@/components/ui/badge';

import { useFolderOperations } from '@/hooks/useFolderOperations';
import { useLibraryProcessingStatus } from '@/hooks/useLibraryProcessingStatus';
import { FolderDetails, isIndexingPending } from '@/types/Folder';
import { ConfirmDialog } from '@/components/ConfirmDialog/ConfirmDialog';
import SettingsCard from './SettingsCard';

/**
 * Component for managing folder operations in settings
 */
const FolderManagementCard: React.FC = () => {
  const {
    folders,
    toggleAITagging,
    deleteFolders,
    enableAITaggingPending,
    disableAITaggingPending,
    deleteFoldersPending,
  } = useFolderOperations();

  const taggingStatus = useSelector(
    (state: RootState) => state.folders.taggingStatus,
  );

  const { semanticAvailable } = useLibraryProcessingStatus();

  const [visibleFoldersCount, setVisibleFoldersCount] = useState(6);
  const [selectedFolderIds, setSelectedFolderIds] = useState<Set<string>>(
    new Set(),
  );
  // Folders queued for deletion. Empty means the confirmation is closed.
  const [foldersToDelete, setFoldersToDelete] = useState<FolderDetails[]>([]);

  const visibleFolders = folders.slice(0, visibleFoldersCount);
  const selectedFolders = folders.filter((folder: FolderDetails) =>
    selectedFolderIds.has(folder.folder_id),
  );
  const allVisibleSelected =
    visibleFolders.length > 0 &&
    visibleFolders.every((folder: FolderDetails) =>
      selectedFolderIds.has(folder.folder_id),
    );

  const handleViewMore = () => {
    setVisibleFoldersCount((prevCount) => prevCount + 5);
  };

  const toggleFolderSelection = (folderId: string) => {
    setSelectedFolderIds((previous) => {
      const next = new Set(previous);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  };

  // Only spans the folders currently on screen, so "View More" never pulls in
  // folders the user has not seen.
  const toggleSelectAllVisible = () => {
    setSelectedFolderIds((previous) => {
      const next = new Set(previous);
      visibleFolders.forEach((folder: FolderDetails) => {
        if (allVisibleSelected) {
          next.delete(folder.folder_id);
        } else {
          next.add(folder.folder_id);
        }
      });
      return next;
    });
  };

  const confirmDeletion = () => {
    deleteFolders(foldersToDelete.map((folder) => folder.folder_id));
    setSelectedFolderIds((previous) => {
      const next = new Set(previous);
      foldersToDelete.forEach((folder) => next.delete(folder.folder_id));
      return next;
    });
  };

  const deletionDescription = () => {
    if (foldersToDelete.length === 1) {
      return `"${foldersToDelete[0].folder_path}" will be removed from your library along with its tags and indexing data. This cannot be undone, though the photos themselves stay on your disk.`;
    }
    return `${foldersToDelete.length} folders will be removed from your library along with their tags and indexing data. This cannot be undone, though the photos themselves stay on your disk.`;
  };

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {folders.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <label className="text-muted-foreground flex cursor-pointer items-center gap-3 text-sm">
              <input
                type="checkbox"
                checked={allVisibleSelected}
                onChange={toggleSelectAllVisible}
                className="border-border h-4 w-4 shrink-0 cursor-pointer rounded"
              />
              Select all
            </label>

            {selectedFolders.length > 0 && (
              <Button
                onClick={() => setFoldersToDelete(selectedFolders)}
                variant="outline"
                size="sm"
                className="cursor-pointer text-red-600 hover:border-red-300 hover:text-red-700 dark:text-red-400"
                disabled={deleteFoldersPending}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete selected ({selectedFolders.length})
              </Button>
            )}
          </div>

          {visibleFolders.map((folder: FolderDetails) => (
            <div
              key={folder.folder_id}
              className="group border-border bg-background/50 relative rounded-lg border p-4 transition-all hover:border-gray-300 hover:shadow-sm dark:hover:border-gray-600"
            >
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={selectedFolderIds.has(folder.folder_id)}
                      onChange={() => toggleFolderSelection(folder.folder_id)}
                      aria-label={`Select folder ${folder.folder_path}`}
                      className="border-border h-4 w-4 shrink-0 cursor-pointer rounded"
                    />
                    <Folder className="h-4 w-4 shrink-0 text-gray-500 dark:text-gray-400" />
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
                    onClick={() => setFoldersToDelete([folder])}
                    aria-label={`Delete folder ${folder.folder_path}`}
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 cursor-pointer text-gray-500 hover:border-red-300 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                    disabled={deleteFoldersPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {folder.AI_Tagging && (
                <div className="mt-3">
                  {isIndexingPending(folder.indexing_status) ? (
                    <div className="flex items-center gap-4 [--radius:1.2rem]">
                      <Badge className="bg-zinc-900 text-white hover:bg-black/90">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Indexing Folder...
                      </Badge>
                    </div>
                  ) : folder.indexing_status === 'interrupted' ? (
                    // A previous session died mid-walk, so nothing is
                    // running and the folder is only partly indexed.
                    <div className="flex items-center gap-4 [--radius:1.2rem]">
                      <Badge variant="outline" className="text-amber-600">
                        <AlertTriangle className="h-4 w-4" />
                        Indexing was interrupted - sync to finish
                      </Badge>
                    </div>
                  ) : !folder.image_count && !folder.video_count ? (
                    <div className="text-muted-foreground text-sm italic">
                      Folder is empty
                    </div>
                  ) : (
                    <>
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

                      {semanticAvailable && (
                        <>
                          <div className="text-muted-foreground mt-3 mb-1 flex items-center justify-between text-xs">
                            <span>Semantic Indexing</span>
                            <span
                              className={
                                (taggingStatus[folder.folder_id]
                                  ?.embedding_percentage ?? 0) >= 100
                                  ? 'flex items-center gap-1 text-green-500'
                                  : 'text-muted-foreground'
                              }
                            >
                              {(taggingStatus[folder.folder_id]
                                ?.embedding_percentage ?? 0) >= 100 && (
                                <Check className="h-3 w-3" />
                              )}
                              {Math.round(
                                taggingStatus[folder.folder_id]
                                  ?.embedding_percentage ?? 0,
                              )}
                              %
                            </span>
                          </div>
                          <Progress
                            value={
                              taggingStatus[folder.folder_id]
                                ?.embedding_percentage ?? 0
                            }
                            indicatorClassName={
                              (taggingStatus[folder.folder_id]
                                ?.embedding_percentage ?? 0) >= 100
                                ? 'bg-green-500'
                                : 'bg-blue-500'
                            }
                          />
                        </>
                      )}
                    </>
                  )}
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

      {folders.length > visibleFoldersCount && (
        <Button
          onClick={handleViewMore}
          variant="outline"
          className="mt-4 w-full"
        >
          View More
        </Button>
      )}

      <div className="border-border mt-6 border-t pt-6">
        <FolderPicker />
      </div>

      <ConfirmDialog
        open={foldersToDelete.length > 0}
        onOpenChange={(open) => {
          if (!open) setFoldersToDelete([]);
        }}
        title={
          foldersToDelete.length > 1
            ? `Delete ${foldersToDelete.length} folders?`
            : 'Delete this folder?'
        }
        description={foldersToDelete.length > 0 ? deletionDescription() : ''}
        confirmLabel={
          foldersToDelete.length > 1
            ? `Delete ${foldersToDelete.length} Folders`
            : 'Delete Folder'
        }
        destructive
        onConfirm={confirmDeletion}
      />
    </SettingsCard>
  );
};

export default FolderManagementCard;
