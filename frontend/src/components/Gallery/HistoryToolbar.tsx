import { Button } from '@/components/ui/button';
import { Trash2, CheckSquare, Square } from 'lucide-react';

interface HistoryToolbarProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}

export function HistoryToolbar({
  selectedCount,
  totalCount,
  onSelectAll,
  onDelete,
  isDeleting,
}: HistoryToolbarProps) {
  const isAllSelected = selectedCount === totalCount && totalCount > 0;

  return (
    <div className="flex items-center justify-between p-4 border-b">
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onSelectAll}
          disabled={totalCount === 0}
        >
          {isAllSelected ? (
            <>
              <CheckSquare className="h-4 w-4 mr-2" />
              Deselect All
            </>
          ) : (
            <>
              <Square className="h-4 w-4 mr-2" />
              Select All
            </>
          )}
        </Button>
      </div>

      <div className="flex items-center gap-2">
        {selectedCount > 0 && (
          <>
            <span className="text-sm text-muted-foreground">
              {selectedCount} of {totalCount} selected
            </span>
            <Button
              variant="destructive"
              size="sm"
              onClick={onDelete}
              disabled={isDeleting}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {isDeleting ? 'Deleting...' : 'Delete Permanently'}
            </Button>
          </>
        )}
      </div>
    </div>
  );
}