import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';

interface ImageState {
  images: Image[];
  currentViewIndex: number;
  totalImages: number;
  error: string | null;
}

const initialState: ImageState = {
  images: [],
  currentViewIndex: -1,
  totalImages: 0,
  error: null,
};

const imageSlice = createSlice({
  name: 'images',
  initialState,
  reducers: {
    setImages(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
      state.totalImages = action.payload.length;
      state.error = null;
    },
    addImages(state, action: PayloadAction<Image[]>) {
      state.images.push(...action.payload);
      state.totalImages = state.images.length;
    },
    setCurrentViewIndex(state, action: PayloadAction<number>) {
      const index = action.payload;
      if (index >= -1 && index < state.images.length) {
        state.currentViewIndex = index;
      } else {
        console.warn(
          `Invalid image index: ${index}. Valid range: -1 to ${state.images.length - 1}`,
        );
      }
    },
    nextImage(state) {
      if (state.currentViewIndex < state.images.length - 1) {
        state.currentViewIndex += 1;
      }
    },
    previousImage(state) {
      if (state.currentViewIndex > 0) {
        state.currentViewIndex -= 1;
      }
    },
    closeImageView(state) {
      state.currentViewIndex = -1;
    },
    updateImage(
      state,
      action: PayloadAction<{ id: string; updates: Partial<Image> }>,
    ) {
      const { id, updates } = action.payload;
      const imageIndex = state.images.findIndex((image) => image.id === id);
      if (imageIndex !== -1) {
        state.images[imageIndex] = { ...state.images[imageIndex], ...updates };
      }
    },
    removeImage(state, action: PayloadAction<string>) {
      const imageId = action.payload;
      const imageIndex = state.images.findIndex(
        (image) => image.id === imageId,
      );
      if (imageIndex !== -1) {
        state.images.splice(imageIndex, 1);
        state.totalImages = state.images.length;

        // Adjust currentViewIndex if necessary
        if (
          state.currentViewIndex >= imageIndex &&
          state.currentViewIndex > 0
        ) {
          state.currentViewIndex -= 1;
        } else if (state.currentViewIndex >= state.images.length) {
          state.currentViewIndex = state.images.length - 1;
        }
      }
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    clearImages(state) {
      state.images = [];
      state.currentViewIndex = -1;
      state.totalImages = 0;
      state.error = null;
    },
  },
});

export const {
  setImages,
  addImages,
  setCurrentViewIndex,
  nextImage,
  previousImage,
  closeImageView,
  updateImage,
  removeImage,
  setError,
  clearImages,
} = imageSlice.actions;

export default imageSlice.reducer;
