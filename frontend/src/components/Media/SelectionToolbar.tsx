import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  selectSelectedImageCount,
  selectSelectedImageIds,
} from '@/features/albumSelectors';
import {
  clearSelectedImages,
  disableSelectionMode,
  selectAllImages,
} from '@/features/albumSlice';
import { selectImages } from '@/features/imageSelectors';
import {
  Download,
  FolderPlus,
  RotateCcw,
  SelectAll,
  Share2,
  Trash2,
  X,
} from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';

interface SelectionToolbarProps {
  onAddToAlbum?: () => void;
  onCreateNewAlbum?: () => void;
  onRemoveFromAlbum?: () => void;
  onDownload?: () => void;
  onShare?: () => void;
  onDelete?: () => void;
  showAlbumActions?: boolean;
  showRemoveFromAlbum?: boolean;
}

export function SelectionToolbar({
  onAddToAlbum,
  onCreateNewAlbum,
  onRemoveFromAlbum,
  onDownload,
  onShare,
  onDelete,
  showAlbumActions = true,
  showRemoveFromAlbum = false,
}: SelectionToolbarProps) {
  const dispatch = useDispatch();
  const selectedCount = useSelector(selectSelectedImageCount);
  const selectedImageIds = useSelector(selectSelectedImageIds);
  const allImages = useSelector(selectImages);

  const handleClose = () => {
    dispatch(disableSelectionMode());
  };

  const handleClearSelection = () => {
    dispatch(clearSelectedImages());
  };

  const handleSelectAll = () => {
    const allImageIds = allImages.map((image: any) => image.id);
    dispatch(selectAllImages(allImageIds));
  };

  const isAllSelected =
    selectedImageIds.length === allImages.length && allImages.length > 0;

  return (
    <Card className="fixed bottom-4 left-1/2 z-50 flex max-w-[95vw] -translate-x-1/2 transform items-center gap-2 overflow-x-auto p-3 shadow-lg">
      {/* Selection count */}
      <Badge variant="secondary" className="px-3 py-1">
        {selectedCount} selected
      </Badge>

      {/* Select all / Clear selection */}
      <Button
        variant="outline"
        size="sm"
        onClick={isAllSelected ? handleClearSelection : handleSelectAll}
        className="gap-2"
      >
        {isAllSelected ? (
          <>
            <RotateCcw className="h-4 w-4" />
            Clear All
          </>
        ) : (
          <>
            <SelectAll className="h-4 w-4" />
            Select All
          </>
        )}
      </Button>

      {/* Divider */}
      <div className="bg-border h-6 w-px" />

      {/* Album actions */}
      {showAlbumActions && (
        <>
          <Button
            variant="outline"
            size="sm"
            onClick={onAddToAlbum}
            className="gap-2"
            disabled={selectedCount === 0}
          >
            <FolderPlus className="h-4 w-4" />
            Add to Album
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onCreateNewAlbum}
            className="gap-2"
            disabled={selectedCount === 0}
          >
            <FolderPlus className="h-4 w-4" />
            New Album
          </Button>
        </>
      )}

      {/* Remove from album (only show in album view) */}
      {showRemoveFromAlbum && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRemoveFromAlbum}
          className="gap-2"
          disabled={selectedCount === 0}
        >
          <Trash2 className="h-4 w-4" />
          Remove from Album
        </Button>
      )}

      {/* Other actions */}
      <Button
        variant="outline"
        size="sm"
        onClick={onDownload}
        className="gap-2"
        disabled={selectedCount === 0}
      >
        <Download className="h-4 w-4" />
        Download
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={onShare}
        className="gap-2"
        disabled={selectedCount === 0}
      >
        <Share2 className="h-4 w-4" />
        Share
      </Button>

      {/* Delete */}
      <Button
        variant="destructive"
        size="sm"
        onClick={onDelete}
        className="gap-2"
        disabled={selectedCount === 0}
      >
        <Trash2 className="h-4 w-4" />
        Delete
      </Button>

      {/* Close button */}
      <Button variant="ghost" size="sm" onClick={handleClose} className="ml-2">
        <X className="h-4 w-4" />
      </Button>
    </Card>
  );
}
