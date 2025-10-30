import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectImages = (state: RootState) => {
  return state.images.images;
};

export const selectCurrentViewIndex = (state: RootState) =>
  state.images.currentViewIndex;

// Memoized selectors
export const selectIsImageViewOpen = createSelector(
  [selectCurrentViewIndex],
  (currentIndex) => currentIndex >= 0,
);
