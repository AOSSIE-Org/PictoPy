import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  Folder,
  Loader2,
  Trash2,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

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
import SettingsCard from './SettingsCard';

type TaggingStatus = RootState['folders']['taggingStatus'];

// A single labeled progress bar with a percentage.

const ProgressRow: React.FC<{ label: string; percentage: number }> = ({
  label,
  percentage,
}) => {
  const isComplete = percentage >= 100;

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
          {Math.round(percentage)}%
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
    deleteFolder,
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

  // --- NEW: Force data refresh when window regains focus or visibility ---
  useEffect(() => {
    const handleFocus = () => {
      // Invalidating queries forces useLibraryProcessingStatus() to fetch fresh data instantly
      // so semanticAvailable becomes false immediately when coming back from minimizing/another window
      queryClient.invalidateQueries();
    };

    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        handleFocus();
      }
    });

    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleFocus);
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

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {folders.length > 0 ? (
        <div className="space-y-3">
          {folders
            .slice(0, visibleFoldersCount)
            .map((folder: FolderDetails) => (
              <div
                key={folder.folder_id}
                className="group border-border bg-background/50 relative rounded-lg border p-4 transition-all hover:border-gray-300 hover:shadow-sm dark:hover:border-gray-600"
              >
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3">
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
    </SettingsCard>
  );
};

export default FolderManagementCard;
