import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';
import { ImageSource } from './imageSlice';

// Basic selectors
export const selectImages = (state: RootState) => {
  return state.images.images;
};

export const selectCurrentViewIndex = (state: RootState) =>
  state.images.currentViewIndex;

export const selectImageSource = (state: RootState): ImageSource =>
  state.images.source;

// Memoized selectors
export const selectIsImageViewOpen = createSelector(
  [selectCurrentViewIndex],
  (currentIndex) => currentIndex >= 0,
);

/**
 * Returns true if the current images are NOT from the gallery
 * Used to trigger refetch when returning to Home page
 */
export const selectNeedsGalleryRefresh = createSelector(
  [selectImageSource],
  (source) => source !== null && source !== 'gallery',
);
