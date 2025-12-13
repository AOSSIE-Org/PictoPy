import React from 'react';
import {
  ChevronDown,
  ChevronRight,
  Folder,
  Trash2,
  Check,
  CheckCircle2,
  Loader2,
  Clock,
} from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { FolderWithStatus } from '@/utils/folderUtils';

type SectionType = 'completed' | 'inProgress' | 'pending';

interface FolderSectionProps {
  type: SectionType;
  folders: FolderWithStatus[];
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  selectedIds: Set<string>;
  onToggleSelection: (folderId: string) => void;
  onToggleAITagging: (folder: FolderWithStatus) => void;
  onDeleteFolder: (folderId: string) => void;
  isTaggingPending: boolean;
  isDeletePending: boolean;
}

const sectionConfig: Record<
  SectionType,
  { label: string; icon: React.ElementType; color: string }
> = {
  completed: {
    label: 'Completed',
    icon: CheckCircle2,
    color: 'text-green-500',
  },
  inProgress: {
    label: 'In Progress',
    icon: Loader2,
    color: 'text-blue-500',
  },
  pending: {
    label: 'Pending',
    icon: Clock,
    color: 'text-gray-400',
  },
};

/**
 * Collapsible section for grouped folders
 */
export const FolderSection: React.FC<FolderSectionProps> = ({
  type,
  folders,
  isCollapsed,
  onToggleCollapse,
  selectedIds,
  onToggleSelection,
  onToggleAITagging,
  onDeleteFolder,
  isTaggingPending,
  isDeletePending,
}) => {
  if (folders.length === 0) return null;

  const config = sectionConfig[type];
  const Icon = config.icon;

  return (
    <div className="mb-4">
      {/* Section Header */}
      <button
        onClick={onToggleCollapse}
        className="hover:bg-muted/50 mb-2 flex w-full items-center gap-2 rounded-md p-2 transition-colors"
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
        <Icon className={`h-4 w-4 ${config.color}`} />
        <span className="font-medium">{config.label}</span>
        <span className="text-muted-foreground text-sm">({folders.length})</span>
      </button>

      {/* Folder List */}
      {!isCollapsed && (
        <div className="space-y-2 pl-2">
          {folders.map((folder) => (
            <FolderItem
              key={folder.folder_id}
              folder={folder}
              isSelected={selectedIds.has(folder.folder_id)}
              onToggleSelection={() => onToggleSelection(folder.folder_id)}
              onToggleAITagging={() => onToggleAITagging(folder)}
              onDelete={() => onDeleteFolder(folder.folder_id)}
              isTaggingPending={isTaggingPending}
              isDeletePending={isDeletePending}
              showProgress={type !== 'pending'}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface FolderItemProps {
  folder: FolderWithStatus;
  isSelected: boolean;
  onToggleSelection: () => void;
  onToggleAITagging: () => void;
  onDelete: () => void;
  isTaggingPending: boolean;
  isDeletePending: boolean;
  showProgress: boolean;
}

const FolderItem: React.FC<FolderItemProps> = ({
  folder,
  isSelected,
  onToggleSelection,
  onToggleAITagging,
  onDelete,
  isTaggingPending,
  isDeletePending,
  showProgress,
}) => {
  const isComplete = folder.tagging_percentage >= 100;

  return (
    <div
      className={`border-border bg-background/50 group relative rounded-lg border p-3 transition-all hover:border-gray-300 hover:shadow-sm dark:hover:border-gray-600 ${
        isSelected ? 'border-primary bg-primary/5' : ''
      }`}
    >
      <div className="flex items-center gap-3">
        {/* Checkbox */}
        <Checkbox
          checked={isSelected}
          onCheckedChange={onToggleSelection}
          className="cursor-pointer"
        />

        {/* Folder Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Folder className="h-4 w-4 shrink-0 text-gray-500 dark:text-gray-400" />
            <span className="text-foreground truncate text-sm">
              {folder.folder_path}
            </span>
          </div>

          {/* Progress Bar */}
          {showProgress && folder.AI_Tagging && (
            <div className="mt-2">
              <div className="text-muted-foreground mb-1 flex items-center justify-between text-xs">
                <span>Progress</span>
                <span
                  className={
                    isComplete
                      ? 'flex items-center gap-1 text-green-500'
                      : 'text-muted-foreground'
                  }
                >
                  {isComplete && <Check className="h-3 w-3" />}
                  {Math.round(folder.tagging_percentage)}%
                </span>
              </div>
              <Progress
                value={folder.tagging_percentage}
                className="h-1.5"
                indicatorClassName={isComplete ? 'bg-green-500' : 'bg-blue-500'}
              />
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground text-xs">AI</span>
            <Switch
              className="cursor-pointer"
              checked={folder.AI_Tagging}
              onCheckedChange={onToggleAITagging}
              disabled={isTaggingPending}
            />
          </div>

          <Button
            onClick={onDelete}
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-gray-400 hover:text-red-500"
            disabled={isDeletePending}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default FolderSection;
