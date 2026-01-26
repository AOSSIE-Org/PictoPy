import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';

interface ImageState {
  images: Image[];
  currentViewIndex: number;
  selectedImages: string[]; // Array of selected image IDs
  isSelectionMode: boolean; // Whether selection mode is active
  
  lastDeletedImages: string[];
  showUndo: boolean;
}

const initialState: ImageState = {
  images: [],
  currentViewIndex: -1,
  selectedImages: [],
  isSelectionMode: false,
  
  lastDeletedImages: [],
  showUndo: false,
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
      state.selectedImages = [];
      state.isSelectionMode = false;
    },

    // Selection mode reducers
    toggleSelectionMode(state) {
      state.isSelectionMode = !state.isSelectionMode;
      if (!state.isSelectionMode) {
        state.selectedImages = [];
      }
    },

    selectImage(state, action: PayloadAction<string>) {
      const imageId = action.payload;
      if (!state.selectedImages.includes(imageId)) {
        state.selectedImages.push(imageId);
      }
    },

    deselectImage(state, action: PayloadAction<string>) {
      state.selectedImages = state.selectedImages.filter(id => id !== action.payload);
    },

    toggleImageSelection(state, action: PayloadAction<string>) {
      const imageId = action.payload;
      const index = state.selectedImages.indexOf(imageId);
      if (index > -1) {
        state.selectedImages.splice(index, 1);
      } else {
        state.selectedImages.push(imageId);
      }
    },

    selectAllImages(state) {
      state.selectedImages = state.images.map(img => img.id);
    },

    deselectAllImages(state) {
      state.selectedImages = [];
    },

    // Soft delete/restore actions
    markImagesAsDeleted(state, action: PayloadAction<string[]>) {
      const imageIds = action.payload;
      state.images = state.images.map(img =>
        imageIds.includes(img.id)
          ? { ...img, is_deleted: true, deleted_at: new Date().toISOString() }
          : img
      );
      state.selectedImages = state.selectedImages.filter(id => !imageIds.includes(id));
    },

    markImagesAsRestored(state, action: PayloadAction<string[]>) {
      const imageIds = action.payload;
      state.images = state.images.map(img =>
        imageIds.includes(img.id)
          ? { ...img, is_deleted: false, deleted_at: undefined }
          : img
      );
    },


    setUndoState(state, action: PayloadAction<string[]>) {
  state.lastDeletedImages = action.payload;
  state.showUndo = true;
},

clearUndoState(state) {
  state.lastDeletedImages = [];
  state.showUndo = false;
},

  },
});

export const {
  setImages,
  setCurrentViewIndex,
  closeImageView,
  clearImages,
  toggleSelectionMode,
  selectImage,
  deselectImage,
  toggleImageSelection,
  selectAllImages,
  deselectAllImages,
  markImagesAsDeleted,
  markImagesAsRestored,
   setUndoState,
  clearUndoState,
} = imageSlice.actions;

export default imageSlice.reducer;
