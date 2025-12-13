import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Card } from '@/components/ui/card';
import { Folder, CheckSquare, Tag, Loader2 } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/app/hooks';
import {
  selectAllFolders,
  deselectAllFolders,
  toggleFolderSelection,
} from '@/features/bulkTagging/bulkTaggingSlice';

interface BulkTaggingControlsProps {
  onBulkTag: (folderIds: string[]) => Promise<void>;
  folders: Array<{ id: string; name: string; aiTaggingEnabled: boolean }>;
}

export const BulkTaggingControls: React.FC<BulkTaggingControlsProps> = ({
  onBulkTag,
  folders,
}) => {
  const dispatch = useAppDispatch();
  const selectedFolderIds = useAppSelector(
    (state) => state.bulkTagging.selectedFolderIds
  );
  const [isTagging, setIsTagging] = useState(false);

  const allSelected =
    folders.length > 0 && selectedFolderIds.length === folders.length;

  const handleSelectAll = () => {
    if (allSelected) {
      dispatch(deselectAllFolders());
    } else {
      dispatch(selectAllFolders(folders.map((f) => f.id)));
    }
  };

  const handleBulkTagAll = async () => {
    setIsTagging(true);
    try {
      await onBulkTag(folders.map((f) => f.id));
    } finally {
      setIsTagging(false);
    }
  };

  const handleTagSelected = async () => {
    if (selectedFolderIds.length === 0) return;
    setIsTagging(true);
    try {
      await onBulkTag(selectedFolderIds);
    } finally {
      setIsTagging(false);
    }
  };

  return (
    <Card className="p-4 mb-4 bg-muted/50">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Checkbox
            checked={allSelected}
            onCheckedChange={handleSelectAll}
            id="select-all"
          />
          <label
            htmlFor="select-all"
            className="text-sm font-medium cursor-pointer"
          >
            Select All ({selectedFolderIds.length}/{folders.length})
          </label>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={handleTagSelected}
            disabled={selectedFolderIds.length === 0 || isTagging}
            variant="default"
            size="sm"
          >
            {isTagging ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Tag className="mr-2 h-4 w-4" />
            )}
            Tag Selected ({selectedFolderIds.length})
          </Button>

          <Button
            onClick={handleBulkTagAll}
            disabled={folders.length === 0 || isTagging}
            variant="secondary"
            size="sm"
          >
            {isTagging ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Folder className="mr-2 h-4 w-4" />
            )}
            AI Tag All
          </Button>
        </div>
      </div>
    </Card>
  );
};
