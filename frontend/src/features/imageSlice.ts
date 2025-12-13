import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';

/**
 * Source types for tracking where images came from
 * This prevents state pollution when navigating between views
 */
export type ImageSource = 'gallery' | 'cluster' | 'search' | 'album' | null;

interface ImageState {
  images: Image[];
  currentViewIndex: number;
  /** Tracks the source of current images to prevent state pollution */
  source: ImageSource;
}

const initialState: ImageState = {
  images: [],
  currentViewIndex: -1,
  source: null,
};

const imageSlice = createSlice({
  name: 'images',
  initialState,
  reducers: {
    /**
     * Sets images with source tracking
     * @deprecated Use setGalleryImages or setClusterImages instead for clarity
     */
    setImages(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
    },

    /** Sets images from the main gallery */
    setGalleryImages(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
      state.source = 'gallery';
    },

    /** Sets images from a face cluster view */
    setClusterImages(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
      state.source = 'cluster';
    },

    /** Sets images from search results */
    setSearchImages(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
      state.source = 'search';
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
      state.source = null;
    },
  },
});

export const {
  setImages,
  setGalleryImages,
  setClusterImages,
  setSearchImages,
  setCurrentViewIndex,
  closeImageView,
  clearImages,
} = imageSlice.actions;

export default imageSlice.reducer;
