import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectVideos = (state: RootState) => {
  return state.videos.videos;
};

export const selectCurrentVideoIndex = (state: RootState) =>
  state.videos.currentViewIndex;

// Memoized selectors
export const selectIsVideoViewOpen = createSelector(
  [selectCurrentVideoIndex],
  (currentIndex) => currentIndex >= 0,
);
