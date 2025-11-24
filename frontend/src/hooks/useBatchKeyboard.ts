import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import {
  selectAllImages,
  deselectAllImages,
} from '@/store/slices/selectionSlice';

export const useBatchKeyboard = (allImageIds: string[]) => {
  const dispatch = useDispatch();
  const { isSelectionMode } = useSelector(
    (state: RootState) => state.selection
  );

  const { selectedImageIds } = useSelector(
    (state: RootState) => state.selection
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isSelectionMode) return;

      // Ctrl+A: Toggle between select all and deselect all
      if (e.ctrlKey && e.key === 'a') {
        e.preventDefault();
        // If all images are selected, deselect all; otherwise select all
        if (selectedImageIds.length === allImageIds.length && allImageIds.length > 0) {
          dispatch(deselectAllImages());
        } else {
          dispatch(selectAllImages(allImageIds));
        }
      }

      // Escape: Deselect all
      if (e.key === 'Escape') {
        e.preventDefault();
        dispatch(deselectAllImages());
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSelectionMode, allImageIds, selectedImageIds, dispatch]);
};
