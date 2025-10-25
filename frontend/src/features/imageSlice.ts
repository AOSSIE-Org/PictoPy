import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';

interface ImageState {
  images: Image[];
  viewerImages: Image[] | null;
  currentViewIndex: number;
  totalImages: number;
  error: string | null;
}

const initialState: ImageState = {
  images: [],
  viewerImages: null,
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
    setViewerContent(
      state,
      action: PayloadAction<{ images: Image[]; index: number }>,
    ) {
      const { images, index } = action.payload;
      if (index >= 0 && index < images.length) {
        state.viewerImages = images;
        state.currentViewIndex = index;
      } else {
        console.warn(
          `Invalid index provided to setViewerContent: ${index}. Valid range: 0 to ${
            images.length - 1
          }`,
        );
      }
    },
    addImages(state, action: PayloadAction<Image[]>) {
      state.images.push(...action.payload);
      state.totalImages = state.images.length;
    },
    setCurrentViewIndex(state, action: PayloadAction<number>) {
      const imageList = state.viewerImages ?? state.images;
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
      state.viewerImages = null;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    clearImages(state) {
      state.images = [];
      state.currentViewIndex = -1;
      state.totalImages = 0;
      state.error = null;
      state.viewerImages = null;
    },
  },
});

export const {
  setImages,
  setViewerContent,
  addImages,
  setCurrentViewIndex,
  closeImageView,
  setError,
  clearImages,
} = imageSlice.actions;

export default imageSlice.reducer;
