import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';
import { PaginationInfo } from '@/types/API';

interface PaginationState {
  page: number;
  limit: number;
  totalCount: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
  isLoadingMore: boolean;
}

interface ImageState {
  images: Image[];
  currentViewIndex: number;
  pagination: PaginationState;
}

const initialPaginationState: PaginationState = {
  page: 1,
  limit: 50,
  totalCount: 0,
  totalPages: 0,
  hasNext: false,
  hasPrevious: false,
  isLoadingMore: false,
};

const initialState: ImageState = {
  images: [],
  currentViewIndex: -1,
  pagination: initialPaginationState,
};

const imageSlice = createSlice({
  name: 'images',
  initialState,
  reducers: {
    setImages(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
    },

    // Append images for infinite scroll (adds to existing images)
    appendImages(state, action: PayloadAction<Image[]>) {
      state.images = [...state.images, ...action.payload];
    },

    // Set pagination info from API response
    setPagination(state, action: PayloadAction<PaginationInfo>) {
      state.pagination = {
        page: action.payload.page,
        limit: action.payload.limit,
        totalCount: action.payload.total_count,
        totalPages: action.payload.total_pages,
        hasNext: action.payload.has_next,
        hasPrevious: action.payload.has_previous,
        isLoadingMore: false,
      };
    },

    // Set loading state for infinite scroll
    setLoadingMore(state, action: PayloadAction<boolean>) {
      state.pagination.isLoadingMore = action.payload;
    },

    // Increment page for next fetch
    incrementPage(state) {
      if (state.pagination.hasNext) {
        state.pagination.page += 1;
      }
    },

    // Reset pagination to initial state
    resetPagination(state) {
      state.pagination = initialPaginationState;
    },

    setCurrentViewIndex(state, action: PayloadAction<number>) {
      const imageList = state.images;
      const index = action.payload;
      if (index >= -1 && index < imageList.length) {
        state.currentViewIndex = index;
      } else {
        console.warn(
          `Invalid image index: ${index}. Valid range: -1 to ${
            imageList.length - 1
          }`,
        );
      }
    },
    closeImageView(state) {
      state.currentViewIndex = -1;
    },

    clearImages(state) {
      state.images = [];
      state.currentViewIndex = -1;
      state.pagination = initialPaginationState;
    },
  },
});

export const {
  setImages,
  appendImages,
  setPagination,
  setLoadingMore,
  incrementPage,
  resetPagination,
  setCurrentViewIndex,
  closeImageView,
  clearImages,
} = imageSlice.actions;

export default imageSlice.reducer;
