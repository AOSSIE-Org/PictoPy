import React from 'react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  X,
  Trash2,
  Heart,
  Download,
  CheckSquare,
} from 'lucide-react';

interface BatchOperationsToolbarProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onMarkFavorite: () => void;
  onUnmarkFavorite: () => void;
  onDelete: () => void;
  onDownload?: () => void;
}

export const BatchOperationsToolbar: React.FC<BatchOperationsToolbarProps> = ({
  selectedCount,
  totalCount,
  onSelectAll,
  onDeselectAll,
  onMarkFavorite,
  onUnmarkFavorite,
  onDelete,
  onDownload,
}) => {
  if (selectedCount === 0) return null;

  const allSelected = selectedCount === totalCount;

  return (
    <div className="sticky top-0 z-10 bg-blue-600 text-white p-4 mb-4 rounded-lg shadow-lg flex justify-between items-center">
      {/* Left: Selection Count */}
      <div className="flex items-center gap-4">
        <span className="font-bold">
          {selectedCount} image{selectedCount !== 1 ? 's' : ''} selected
        </span>
        <Separator orientation="vertical" className="h-6 bg-white/30" />
        <Button
          variant="ghost"
          size="sm"
          className="text-white hover:bg-white/10"
          onClick={allSelected ? onDeselectAll : onSelectAll}
        >
          <CheckSquare className="h-4 w-4 mr-2" />
          {allSelected ? 'Deselect All' : 'Select All'}
        </Button>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="text-white hover:bg-white/10"
          onClick={onMarkFavorite}
          title="Mark as favorite"
        >
          <Heart className="h-4 w-4 fill-current" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="text-white hover:bg-white/10"
          onClick={onUnmarkFavorite}
          title="Remove from favorites"
        >
          <Heart className="h-4 w-4" />
        </Button>

        {onDownload && (
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/10"
            onClick={onDownload}
            title="Download selected"
          >
            <Download className="h-4 w-4" />
          </Button>
        )}

        <Separator orientation="vertical" className="h-6 bg-white/30" />

        <Button
          variant="ghost"
          size="sm"
          className="text-white hover:bg-red-500/20"
          onClick={onDelete}
          title="Delete selected"
        >
          <Trash2 className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="text-white hover:bg-white/10"
          onClick={onDeselectAll}
          title="Clear selection"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};