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

    clearImages(state) {
      state.images = [];
      state.currentViewIndex = -1;
    },
  },
});

export const { setImages, setCurrentViewIndex, closeImageView, clearImages } =
  imageSlice.actions;

export default imageSlice.reducer;
