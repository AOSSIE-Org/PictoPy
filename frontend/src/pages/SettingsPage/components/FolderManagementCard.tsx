import React, { useMemo, useState } from 'react';
import { Folder, Trash2, Check } from 'lucide-react';

import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import FolderPicker from '@/components/FolderPicker/FolderPicker';

import { useFolderOperations } from '@/hooks/useFolderOperations';
import { FolderDetails } from '@/types/Folder';
import SettingsCard from './SettingsCard';

const getFolderProgress = (
  folder: FolderDetails,
  taggingStatus?: { tagging_percentage?: number },
) => {
  if (folder.taggingCompleted) return 100;
  if (typeof taggingStatus?.tagging_percentage === 'number') {
    return Math.max(
      0,
      Math.min(100, Math.round(taggingStatus.tagging_percentage)),
    );
  }
  return 0;
};

/**
 * Component for managing folder operations in settings
 */
const FolderManagementCard: React.FC = () => {
  const {
    folders,
    toggleAITagging,
    deleteFolder,
    tagAllFolders,
    tagSelectedFolders,
    enableAITaggingPending,
    disableAITaggingPending,
    deleteFolderPending,
    bulkEnablePending,
  } = useFolderOperations();

  const taggingStatus = useSelector(
    (state: RootState) => state.folders.taggingStatus,
  );

  // Local selection state
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const allSelected = useMemo(
    () => folders.length > 0 && folders.every((f) => selected[f.folder_id]),
    [folders, selected],
  );

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelected({});
    } else {
      const map: Record<string, boolean> = {};
      folders.forEach((f) => (map[f.folder_id] = true));
      setSelected(map);
    }
  };

  const selectedIds = useMemo(
    () =>
      Object.entries(selected)
        .filter(([, v]) => v)
        .map(([id]) => id),
    [selected],
  );

  // Sorting into groups with progress: Completed, In Progress, Pending
  // This enriches each folder with its progress percentage for use by totals
  const groups = useMemo(() => {
    const completed: Array<FolderDetails & { progress: number }> = [];
    const inProgress: Array<FolderDetails & { progress: number }> = [];
    const pending: Array<FolderDetails & { progress: number }> = [];

    folders.forEach((f) => {
      const progress = getFolderProgress(f, taggingStatus[f.folder_id]);
      const folderWithProgress = { ...f, progress };

      if (f.AI_Tagging) {
        if (progress >= 100) {
          completed.push(folderWithProgress);
        } else {
          inProgress.push(folderWithProgress);
        }
      } else {
        pending.push(folderWithProgress);
      }
    });

    return { completed, inProgress, pending };
  }, [folders, taggingStatus]);

  // Calculate totals using only grouped data
  // No direct access to folders or taggingStatus - all data comes through groups
  const totals = useMemo(() => {
    const completedCount = groups.completed.length;
    const inProgressCount = groups.inProgress.length;
    const pendingCount = groups.pending.length;
    const total = completedCount + inProgressCount + pendingCount;
    const taggedCount = completedCount + inProgressCount; // AI_Tagging enabled

    // Calculate progress sum from pre-computed progress in groups
    const progressSum =
      groups.completed.reduce((acc, folder) => acc + folder.progress, 0) +
      groups.inProgress.reduce((acc, folder) => acc + folder.progress, 0) +
      groups.pending.reduce((acc, folder) => acc + folder.progress, 0);

    const progressPct = total > 0 ? Math.round(progressSum / total) : 0;
    return {
      total,
      completedCount,
      inProgressCount,
      pendingCount,
      taggedCount,
      progressPct,
    };
  }, [groups]);

  const [showCompleted, setShowCompleted] = useState(true);
  const [showInProgress, setShowInProgress] = useState(true);
  const [showPending, setShowPending] = useState(true);

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {folders.length > 0 ? (
        <>
          {/* Progress Summary & Bulk Controls */}
          <div className="border-border mb-4 flex flex-col gap-3 rounded-lg border p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-foreground text-sm font-medium">
                  AI Tagging Progress: {totals.taggedCount}/{totals.total}{' '}
                  folders tagged ({totals.progressPct}%)
                </div>
                <div className="text-muted-foreground text-xs">
                  Completed: {totals.completedCount} | In Progress:{' '}
                  {totals.inProgressCount} | Pending: {totals.pendingCount}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={toggleSelectAll}
                  disabled={folders.length === 0}
                >
                  {allSelected ? 'Unselect All' : 'Select All'}
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={tagAllFolders}
                  disabled={
                    bulkEnablePending || folders.every((f) => f.AI_Tagging)
                  }
                >
                  AI Tag All
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => tagSelectedFolders(selectedIds)}
                  disabled={bulkEnablePending || selectedIds.length === 0}
                >
                  Tag Selected
                </Button>
              </div>
            </div>
            <Progress value={totals.progressPct} />
          </div>

          {/* Smart Sorting Groups */}
          <div className="space-y-4">
            {/* Completed */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-foreground text-sm font-semibold">
                  Completed (AI tagged)
                </h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowCompleted((v) => !v)}
                >
                  {showCompleted ? 'Collapse' : 'Expand'}
                </Button>
              </div>
              {showCompleted && (
                <div className="space-y-3">
                  {groups.completed.map((folder: FolderDetails) => (
                    <FolderRow
                      key={folder.folder_id}
                      folder={folder}
                      taggingStatus={taggingStatus[folder.folder_id]}
                      selected={!!selected[folder.folder_id]}
                      onToggleSelect={() =>
                        setSelected((prev) => ({
                          ...prev,
                          [folder.folder_id]: !prev[folder.folder_id],
                        }))
                      }
                      toggleAITagging={toggleAITagging}
                      deleteFolder={deleteFolder}
                      enableAITaggingPending={enableAITaggingPending}
                      disableAITaggingPending={disableAITaggingPending}
                      deleteFolderPending={deleteFolderPending}
                    />
                  ))}
                  {groups.completed.length === 0 && (
                    <div className="text-muted-foreground text-xs">
                      No completed folders
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* In Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-foreground text-sm font-semibold">
                  In Progress (tagging...)
                </h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowInProgress((v) => !v)}
                >
                  {showInProgress ? 'Collapse' : 'Expand'}
                </Button>
              </div>
              {showInProgress && (
                <div className="space-y-3">
                  {groups.inProgress.map((folder: FolderDetails) => (
                    <FolderRow
                      key={folder.folder_id}
                      folder={folder}
                      taggingStatus={taggingStatus[folder.folder_id]}
                      selected={!!selected[folder.folder_id]}
                      onToggleSelect={() =>
                        setSelected((prev) => ({
                          ...prev,
                          [folder.folder_id]: !prev[folder.folder_id],
                        }))
                      }
                      toggleAITagging={toggleAITagging}
                      deleteFolder={deleteFolder}
                      enableAITaggingPending={enableAITaggingPending}
                      disableAITaggingPending={disableAITaggingPending}
                      deleteFolderPending={deleteFolderPending}
                    />
                  ))}
                  {groups.inProgress.length === 0 && (
                    <div className="text-muted-foreground text-xs">
                      No folders are currently tagging
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Pending */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-foreground text-sm font-semibold">
                  Pending (not yet tagged)
                </h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowPending((v) => !v)}
                >
                  {showPending ? 'Collapse' : 'Expand'}
                </Button>
              </div>
              {showPending && (
                <div className="space-y-3">
                  {groups.pending.map((folder: FolderDetails) => (
                    <FolderRow
                      key={folder.folder_id}
                      folder={folder}
                      taggingStatus={taggingStatus[folder.folder_id]}
                      selected={!!selected[folder.folder_id]}
                      onToggleSelect={() =>
                        setSelected((prev) => ({
                          ...prev,
                          [folder.folder_id]: !prev[folder.folder_id],
                        }))
                      }
                      toggleAITagging={toggleAITagging}
                      deleteFolder={deleteFolder}
                      enableAITaggingPending={enableAITaggingPending}
                      disableAITaggingPending={disableAITaggingPending}
                      deleteFolderPending={deleteFolderPending}
                    />
                  ))}
                  {groups.pending.length === 0 && (
                    <div className="text-muted-foreground text-xs">
                      No pending folders
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
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

// Reusable row component for a folder item
const FolderRow: React.FC<{
  folder: FolderDetails;
  taggingStatus?: { tagging_percentage?: number };
  selected: boolean;
  onToggleSelect: () => void;
  toggleAITagging: (folder: FolderDetails) => void;
  deleteFolder: (folderId: string) => void;
  enableAITaggingPending: boolean;
  disableAITaggingPending: boolean;
  deleteFolderPending: boolean;
}> = ({
  folder,
  taggingStatus,
  selected,
  onToggleSelect,
  toggleAITagging,
  deleteFolder,
  enableAITaggingPending,
  disableAITaggingPending,
  deleteFolderPending,
}) => {
  const percentage = getFolderProgress(folder, taggingStatus);
  const isComplete = percentage >= 100;
  return (
    <div className="group border-border bg-background/50 relative rounded-lg border p-4 transition-all hover:border-gray-300 hover:shadow-sm dark:hover:border-gray-600">
      <div className="flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            {/* Selection checkbox */}
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300"
              checked={selected}
              onChange={onToggleSelect}
            />
            <Folder className="h-4 w-4 flex-shrink-0 text-gray-500 dark:text-gray-400" />
            <span className="text-foreground truncate">
              {folder.folder_path}
            </span>
          </div>
        </div>

        <div className="ml-4 flex items-center gap-4">
          <div className="flex items-center gap-3">
            <span className="text-muted-foreground text-sm">AI Tagging</span>
            <Switch
              className="cursor-pointer"
              checked={folder.AI_Tagging}
              onCheckedChange={() => toggleAITagging(folder)}
              disabled={enableAITaggingPending || disableAITaggingPending}
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
                isComplete
                  ? 'flex items-center gap-1 text-green-500'
                  : 'text-muted-foreground'
              }
            >
              {isComplete && <Check className="h-3 w-3" />}
              {percentage}%
            </span>
          </div>
          <Progress
            value={percentage}
            indicatorClassName={isComplete ? 'bg-green-500' : 'bg-blue-500'}
          />
        </div>
      )}
    </div>
  );
};

export default FolderManagementCard;
