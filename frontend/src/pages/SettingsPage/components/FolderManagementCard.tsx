import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  Folder,
  Loader2,
  Minus,
  Trash2,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import FolderPicker from '@/components/FolderPicker/FolderPicker';
import { ConfirmDialog } from '@/components/ConfirmDialog/ConfirmDialog';
import { cn } from '@/lib/utils';

import { Badge } from '@/components/ui/badge';

import { useFolderOperations } from '@/hooks/useFolderOperations';
import { useLibraryProcessingStatus } from '@/hooks/useLibraryProcessingStatus';
import { FolderDetails, isIndexingPending } from '@/types/Folder';
import SettingsCard from './SettingsCard';

type TaggingStatus = RootState['folders']['taggingStatus'];

// A single labeled progress bar with a percentage.

const ProgressRow: React.FC<{ label: string; percentage: number }> = ({
  label,
  percentage,
}) => {
  const roundedPercentage = Math.round(percentage);
  const isComplete = roundedPercentage >= 100;
  return (
    <div>
      <div className="text-muted-foreground mb-1 flex items-center justify-between text-xs">
        <span>{label}</span>
        <span
          className={
            isComplete
              ? 'flex items-center gap-1 text-green-500'
              : 'text-muted-foreground'
          }
        >
          {isComplete && <Check className="h-3 w-3" />}
          {roundedPercentage}%
        </span>
      </div>
      <Progress
        value={percentage}
        indicatorClassName={isComplete ? 'bg-green-500' : 'bg-blue-500'}
      />
    </div>
  );
};

//Progress display for a single folder.

const FolderProgress: React.FC<{
  folder: FolderDetails;
  taggingStatus: TaggingStatus;
  semanticAvailable: boolean;
  isExpanded: boolean;
  onToggleExpanded: () => void;
}> = ({
  folder,
  taggingStatus,
  semanticAvailable,
  isExpanded,
  onToggleExpanded,
}) => {
  const taggingPercentage =
    taggingStatus[folder.folder_id]?.tagging_percentage ?? 0;

  if (!semanticAvailable) {
    return (
      <ProgressRow label="AI Tagging Progress" percentage={taggingPercentage} />
    );
  }

  const embeddingPercentage =
    taggingStatus[folder.folder_id]?.embedding_percentage ?? 0;
  const combinedPercentage = (taggingPercentage + embeddingPercentage) / 2;

  return (
    <>
      <ProgressRow label="Overall Progress" percentage={combinedPercentage} />

      <button
        type="button"
        onClick={onToggleExpanded}
        aria-expanded={isExpanded}
        className="text-muted-foreground hover:text-foreground mt-2 flex cursor-pointer items-center gap-1 text-xs transition-colors"
      >
        {isExpanded ? (
          <>
            <ChevronUp className="h-3 w-3" />
            Hide details
          </>
        ) : (
          <>
            <ChevronDown className="h-3 w-3" />
            Show details
          </>
        )}
      </button>

      {isExpanded && (
        <div className="border-border mt-3 space-y-3 border-t pt-3">
          <ProgressRow
            label="AI Tagging Progress"
            percentage={taggingPercentage}
          />
          <ProgressRow
            label="Semantic Indexing"
            percentage={embeddingPercentage}
          />
        </div>
      )}
    </>
  );
};

//  Component for managing folder operations in settings

const FolderManagementCard: React.FC = () => {
  const queryClient = useQueryClient();
  const {
    folders,
    toggleAITagging,
    deleteMultipleFolders,
    enableAITaggingPending,
    disableAITaggingPending,
    deleteFolderPending,
  } = useFolderOperations();

  const taggingStatus = useSelector(
    (state: RootState) => state.folders.taggingStatus,
  );

  const { semanticAvailable } = useLibraryProcessingStatus();

  const [visibleFoldersCount, setVisibleFoldersCount] = useState(6);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(),
  );
  const [selectedFolderIds, setSelectedFolderIds] = useState<Set<string>>(
    new Set(),
  );
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const selectAllCheckboxRef = useRef<HTMLInputElement>(null);

  // Prune any selected folder IDs that are no longer in the folder list
  useEffect(() => {
    const currentFolderIds = new Set(folders.map((f) => f.folder_id));
    setSelectedFolderIds((prev) => {
      let changed = false;
      const next = new Set<string>();
      for (const id of prev) {
        if (currentFolderIds.has(id)) {
          next.add(id);
        } else {
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, [folders]);

  // --- NEW: Force data refresh when window regains focus or visibility ---
  useEffect(() => {
    const handleFocus = () => {
      // Invalidating targeted queries forces useLibraryProcessingStatus() and folder hooks
      // to fetch fresh data instantly without invalidating the entire app cache
      queryClient.invalidateQueries({ queryKey: ['models', 'status'] });
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      queryClient.invalidateQueries({
        queryKey: ['folders', 'tagging-status'],
      });
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        handleFocus();
      }
    };
    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [queryClient]);

  const handleViewMore = () => {
    setVisibleFoldersCount((prevCount) => prevCount + 5);
  };

  const toggleFolderExpanded = (folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  };

  const toggleFolderSelection = (folderId: string) => {
    setSelectedFolderIds((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  };

  const isAllSelected =
    folders.length > 0 && selectedFolderIds.size === folders.length;
  const isSomeSelected =
    selectedFolderIds.size > 0 && selectedFolderIds.size < folders.length;

  useEffect(() => {
    if (selectAllCheckboxRef.current) {
      selectAllCheckboxRef.current.indeterminate = isSomeSelected;
    }
  }, [isSomeSelected]);

  const handleToggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedFolderIds(new Set());
    } else {
      setSelectedFolderIds(new Set(folders.map((f) => f.folder_id)));
    }
  };

  const handleOpenBatchDeleteDialog = () => {
    if (selectedFolderIds.size === 0) return;
    setIsConfirmDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (selectedFolderIds.size === 0) return;

    deleteMultipleFolders(Array.from(selectedFolderIds));
  };

  const deleteCount = selectedFolderIds.size;
  const dialogTitle = `Remove ${deleteCount} folder${deleteCount === 1 ? '' : 's'}?`;
  const dialogDescription = `Are you sure you want to remove the selected ${deleteCount} folder${deleteCount === 1 ? '' : 's'} from your library? Photos and videos inside them will no longer appear in PictoPy. Your files on disk will not be deleted.`;

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {folders.length > 0 ? (
        <div className="space-y-3">
          <div className="border-border flex flex-wrap items-center justify-between gap-2 border-b px-4 pb-3">
            <label className="text-muted-foreground hover:text-foreground group/selectall flex cursor-pointer items-center gap-3 text-sm font-medium select-none">
              <div className="group-hover/selectall:bg-accent/50 relative flex size-8 shrink-0 items-center justify-center rounded-full transition-colors">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  ref={selectAllCheckboxRef}
                  onChange={handleToggleSelectAll}
                  className="peer sr-only"
                  aria-label="Select all folders"
                  disabled={deleteFolderPending}
                />
                <div
                  className={cn(
                    'flex size-5 shrink-0 items-center justify-center rounded-full border transition-all duration-150',
                    'border-muted-foreground/40 bg-background/50 group-hover/selectall:border-primary/80 group-hover/selectall:bg-primary/5',
                    'peer-focus-visible:ring-ring peer-focus-visible:ring-offset-background peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2',
                    (isAllSelected || isSomeSelected) &&
                      'border-primary bg-primary text-primary-foreground group-hover/selectall:border-primary group-hover/selectall:bg-primary shadow-xs',
                    deleteFolderPending && 'cursor-not-allowed opacity-50',
                  )}
                >
                  {isAllSelected && <Check className="size-3 stroke-[3]" />}
                  {isSomeSelected && !isAllSelected && (
                    <Minus className="size-3 stroke-[3]" />
                  )}
                </div>
              </div>
              <span>
                {selectedFolderIds.size > 0
                  ? `${selectedFolderIds.size} of ${folders.length} selected`
                  : `Select all (${folders.length})`}
              </span>
            </label>

            {selectedFolderIds.size > 0 && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleOpenBatchDeleteDialog}
                disabled={deleteFolderPending}
                className="h-8 cursor-pointer gap-1.5 text-xs"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Remove Selected ({selectedFolderIds.size})
              </Button>
            )}
          </div>

          {folders
            .slice(0, visibleFoldersCount)
            .map((folder: FolderDetails) => {
              const isSelected = selectedFolderIds.has(folder.folder_id);
              return (
                <div
                  key={folder.folder_id}
                  data-testid={`folder-item-${folder.folder_id}`}
                  className={cn(
                    'group border-border bg-background/50 hover:border-border/80 relative rounded-lg border p-4 transition-all hover:shadow-xs',
                    isSelected &&
                      'border-primary/60 ring-primary/40 bg-primary/5 dark:bg-primary/10 ring-1',
                  )}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      <label
                        htmlFor={`select-folder-${folder.folder_id}`}
                        className="group/checkbox hover:bg-accent/50 relative flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-full transition-colors"
                        title={isSelected ? 'Deselect folder' : 'Select folder'}
                      >
                        <input
                          id={`select-folder-${folder.folder_id}`}
                          type="checkbox"
                          checked={isSelected}
                          onChange={() =>
                            toggleFolderSelection(folder.folder_id)
                          }
                          className="peer sr-only"
                          aria-label={`Select folder ${folder.folder_path}`}
                          disabled={deleteFolderPending}
                        />
                        <div
                          className={cn(
                            'flex size-5 shrink-0 items-center justify-center rounded-full border transition-all duration-150',
                            'border-muted-foreground/40 bg-background/50 group-hover/checkbox:border-primary/80 group-hover/checkbox:bg-primary/5',
                            'peer-focus-visible:ring-ring peer-focus-visible:ring-offset-background peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2',
                            isSelected &&
                              'border-primary bg-primary text-primary-foreground group-hover/checkbox:border-primary group-hover/checkbox:bg-primary shadow-xs',
                            deleteFolderPending &&
                              'cursor-not-allowed opacity-50',
                          )}
                        >
                          {isSelected && (
                            <Check className="size-3 stroke-[3]" />
                          )}
                        </div>
                      </label>

                      <Folder className="text-muted-foreground h-4 w-4 shrink-0" />
                      <span
                        className="text-foreground truncate text-sm font-medium"
                        title={folder.folder_path}
                      >
                        {folder.folder_path}
                      </span>
                    </div>

                    <div className="flex shrink-0 items-center gap-3">
                      <span className="text-muted-foreground text-sm">
                        AI Tagging
                      </span>
                      <Switch
                        className="cursor-pointer"
                        checked={folder.AI_Tagging}
                        onCheckedChange={() => toggleAITagging(folder)}
                        disabled={
                          enableAITaggingPending ||
                          disableAITaggingPending ||
                          deleteFolderPending
                        }
                      />
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
                        <FolderProgress
                          folder={folder}
                          taggingStatus={taggingStatus}
                          semanticAvailable={semanticAvailable}
                          isExpanded={expandedFolders.has(folder.folder_id)}
                          onToggleExpanded={() =>
                            toggleFolderExpanded(folder.folder_id)
                          }
                        />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      ) : (
        <div className="py-8 text-center">
          <Folder className="text-muted-foreground mx-auto mb-3 h-12 w-12" />
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
        open={isConfirmDialogOpen}
        onOpenChange={setIsConfirmDialogOpen}
        title={dialogTitle}
        description={dialogDescription}
        confirmLabel={deleteFolderPending ? 'Removing...' : 'Remove'}
        onConfirm={handleConfirmDelete}
        destructive
      />
    </SettingsCard>
  );
};

export default FolderManagementCard;
