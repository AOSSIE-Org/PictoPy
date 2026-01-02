import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectImages = (state: RootState) => {
  return state.images.images;
};

export const selectCurrentViewIndex = (state: RootState) =>
  state.images.currentViewIndex;

export const selectSelectedImages = (state: RootState) =>
  state.images.selectedImages;

export const selectIsSelectionMode = (state: RootState) =>
  state.images.isSelectionMode;

export const selectSelectedImagesCount = createSelector(
  [selectSelectedImages],
  (selectedImages) => selectedImages.length,
);

// Memoized selectors
export const selectIsImageViewOpen = createSelector(
  [selectCurrentViewIndex],
  (currentIndex) => currentIndex >= 0,
);

export const selectAreAllImagesSelected = createSelector(
  [selectImages, selectSelectedImages],
  (images, selectedImages) =>
    images.length > 0 && selectedImages.length === images.length,
);

export const selectIsAnyImageSelected = createSelector(
  [selectSelectedImages],
  (selectedImages) => selectedImages.length > 0,
);
