import React from 'react';
import { Sparkles, SparklesIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';

interface FolderBulkActionsProps {
  totalCount: number;
  selectedCount: number;
  pendingCount: number;
  enabledCount: number;
  isAllSelected: boolean;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onEnableAll: () => void;
  onEnableSelected: () => void;
  onDisableAll: () => void;
  onDisableSelected: () => void;
  isEnabling: boolean;
  isDisabling: boolean;
}

/**
 * Bulk action buttons for folder management
 */
export const FolderBulkActions: React.FC<FolderBulkActionsProps> = ({
  totalCount,
  selectedCount,
  pendingCount,
  enabledCount,
  isAllSelected,
  onSelectAll,
  onDeselectAll,
  onEnableAll,
  onEnableSelected,
  onDisableAll,
  onDisableSelected,
  isEnabling,
  isDisabling,
}) => {
  if (totalCount === 0) return null;

  const isLoading = isEnabling || isDisabling;

  return (
    <div className="border-border mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3">
      {/* Selection Controls */}
      <div className="flex items-center gap-3">
        <div
          className="flex cursor-pointer items-center gap-2"
          onClick={isAllSelected ? onDeselectAll : onSelectAll}
        >
          <Checkbox
            checked={isAllSelected}
            onCheckedChange={isAllSelected ? onDeselectAll : onSelectAll}
            className="cursor-pointer"
          />
          <span className="text-sm">
            {isAllSelected ? 'Deselect All' : 'Select All'} ({totalCount})
          </span>
        </div>

        {selectedCount > 0 && (
          <span className="text-muted-foreground text-sm">
            {selectedCount} selected
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        {/* Enable Actions */}
        {pendingCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={onEnableAll}
            disabled={isLoading}
            className="gap-1.5"
          >
            <Sparkles className="h-3.5 w-3.5" />
            AI Tag All ({pendingCount})
          </Button>
        )}

        {selectedCount > 0 && (
          <Button
            variant="default"
            size="sm"
            onClick={onEnableSelected}
            disabled={isLoading}
            className="gap-1.5"
          >
            <SparklesIcon className="h-3.5 w-3.5" />
            Tag Selected ({selectedCount})
          </Button>
        )}

        {/* Disable Actions */}
        {enabledCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDisableAll}
            disabled={isLoading}
            className="text-muted-foreground hover:text-destructive gap-1.5"
          >
            Disable All ({enabledCount})
          </Button>
        )}

        {selectedCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDisableSelected}
            disabled={isLoading}
            className="text-muted-foreground hover:text-destructive gap-1.5"
          >
            Disable Selected
          </Button>
        )}
      </div>
    </div>
  );
};

export default FolderBulkActions;
