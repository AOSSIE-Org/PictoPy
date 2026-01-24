import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectImages = (state: RootState) => {
  return state.images.images;
};

export const selectCurrentViewIndex = (state: RootState) =>
  state.images.currentViewIndex;

// Pagination selectors
export const selectPagination = (state: RootState) => state.images.pagination;

export const selectCurrentPage = (state: RootState) =>
  state.images.pagination.page;

export const selectHasNextPage = (state: RootState) =>
  state.images.pagination.hasNext;

export const selectIsLoadingMore = (state: RootState) =>
  state.images.pagination.isLoadingMore;

export const selectTotalCount = (state: RootState) =>
  state.images.pagination.totalCount;

// Memoized selectors
export const selectIsImageViewOpen = createSelector(
  [selectCurrentViewIndex],
  (currentIndex) => currentIndex >= 0,
);
