import { useDispatch, useSelector } from 'react-redux';
import { Button } from '@/components/ui/button';
import {
  selectIsSelectionMode,
  selectSelectedImagesCount,
  selectAreAllImagesSelected,
  selectIsAnyImageSelected,
  selectImages,
} from '@/features/imageSelectors';
import {
  toggleSelectionMode,
  selectAllImages,
  deselectAllImages,
  markImagesAsDeleted,
  markImagesAsRestored,
  setUndoState,
  clearUndoState,
} from '@/features/imageSlice';
import { Trash2, CheckSquare, Square, X } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { softDeleteImages, restoreImages } from '@/api/api-functions';
import { UndoNotification } from './UndoNotification';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export function GalleryToolbar() {
  const dispatch = useDispatch();

  const isSelectionMode = useSelector(selectIsSelectionMode);
  const selectedCount = useSelector(selectSelectedImagesCount);
  const areAllSelected = useSelector(selectAreAllImagesSelected);
  const isAnySelected = useSelector(selectIsAnyImageSelected);
  const images = useSelector(selectImages);

  const selectedImages = useSelector(
    (state: any) => state.images.selectedImages
  );

  const showUndo = useSelector(
    (state: any) => state.images.showUndo
  );

  const lastDeletedImages = useSelector(
    (state: any) => state.images.lastDeletedImages
  );

  // 🔹 DELETE (soft delete)
  const deleteMutation = useMutation({
    mutationFn: softDeleteImages,
    onSuccess: (data) => {
      if (data.success) {
        dispatch(markImagesAsDeleted(selectedImages));
        dispatch(setUndoState(selectedImages));
        dispatch(toggleSelectionMode());
      }
    },
  });

  useMutationFeedback(deleteMutation, {
    loadingMessage: 'Deleting images...',
    successMessage: `${selectedCount} images moved to recently deleted`,
    showSuccess: true,
  });

  // 🔹 RESTORE (undo)
  const restoreMutation = useMutation({
    mutationFn: restoreImages,
    onSuccess: () => {
      dispatch(markImagesAsRestored(lastDeletedImages));
      dispatch(clearUndoState());
    },
  });

  useMutationFeedback(restoreMutation, {
    loadingMessage: 'Restoring images...',
    successMessage: `${lastDeletedImages.length} images restored`,
    showSuccess: true,
  });

  // ---------------- handlers ----------------

  const handleToggleSelectionMode = () => {
    dispatch(toggleSelectionMode());
  };

  const handleSelectAll = () => {
    if (areAllSelected) {
      dispatch(deselectAllImages());
    } else {
      dispatch(selectAllImages());
    }
  };

  const handleDelete = () => {
    if (selectedCount > 0) {
      deleteMutation.mutate(selectedImages);
    }
  };

  const handleUndo = () => {
    restoreMutation.mutate(lastDeletedImages);
  };

  const handleDismissUndo = () => {
    dispatch(clearUndoState());
  };

  // ---------------- UI ----------------

  if (!isSelectionMode && !showUndo) {
    return (
      <div className="flex items-center justify-between p-4">
        <Button variant="outline" size="sm" onClick={handleToggleSelectionMode}>
          Select
        </Button>
      </div>
    );
  }

  if (showUndo) {
    return (
      <UndoNotification
        message={`${lastDeletedImages.length} images deleted`}
        onUndo={handleUndo}
        onDismiss={handleDismissUndo}
      />
    );
  }

  return (
    <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={handleToggleSelectionMode}>
          <X className="h-4 w-4 mr-2" />
          Cancel
        </Button>

        <Button variant="outline" size="sm" onClick={handleSelectAll}>
          {areAllSelected ? (
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
        <span className="text-sm text-muted-foreground">
          {selectedCount} of {images.length} selected
        </span>

        <Button
          variant="destructive"
          size="sm"
          onClick={handleDelete}
          disabled={!isAnySelected || deleteMutation.isPending}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Delete
        </Button>
      </div>
    </div>
  );
}
