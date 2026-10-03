import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';

interface ImageState {
  images: Image[];
  currentViewIndex: number;
}

const initialState: ImageState = {
  images: [],
  currentViewIndex: -1,
};

const imageSlice = createSlice({
  name: 'images',
  initialState,
  reducers: {
    setImages(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
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

    updateImageFavoriteStatus(state, action: PayloadAction<string>) {
      const imageId = action.payload;
      const image = state.images.find((img) => img.id === imageId);
      if (image) {
        image.isFavourite = !image.isFavourite;
      }
    },

    removeImages(state, action: PayloadAction<string[]>) {
      const removed = new Set(action.payload);
      state.images = state.images.filter((img) => !removed.has(img.id));
      // Keep the viewer on a real image: deleting a middle one shows the next,
      // deleting the last steps back, and deleting the only one closes the viewer.
      if (state.images.length === 0) {
        state.currentViewIndex = -1;
      } else if (state.currentViewIndex > state.images.length - 1) {
        state.currentViewIndex = state.images.length - 1;
      }
    },

    clearImages(state) {
      state.images = [];
      state.currentViewIndex = -1;
    },
  },
});

export const {
  setImages,
  setCurrentViewIndex,
  closeImageView,
  updateImageFavoriteStatus,
  removeImages,
  clearImages,
} = imageSlice.actions;

export default imageSlice.reducer;
