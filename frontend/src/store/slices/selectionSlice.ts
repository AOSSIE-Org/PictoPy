import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SelectionState {
  selectedImageIds: string[];
  isSelectionMode: boolean;
}

const initialState: SelectionState = {
  selectedImageIds: [],
  isSelectionMode: false,
};

const selectionSlice = createSlice({
  name: 'selection',
  initialState,
  reducers: {
    toggleImageSelection: (state, action: PayloadAction<string>) => {
      const imageId = action.payload;
      const index = state.selectedImageIds.indexOf(imageId);
      if (index > -1) {
        state.selectedImageIds.splice(index, 1);
      } else {
        state.selectedImageIds.push(imageId);
      }
    },
    selectAllImages: (state, action: PayloadAction<string[]>) => {
      state.selectedImageIds = action.payload;
    },
    deselectAllImages: (state) => {
      state.selectedImageIds = [];
    },
    setSelectionMode: (state, action: PayloadAction<boolean>) => {
      state.isSelectionMode = action.payload;
      if (!action.payload) {
        state.selectedImageIds = [];
      }
    },
    removeFromSelection: (state, action: PayloadAction<string[]>) => {
      state.selectedImageIds = state.selectedImageIds.filter(
        (id) => !action.payload.includes(id)
      );
    },
  },
});

export const {
  toggleImageSelection,
  selectAllImages,
  deselectAllImages,
  setSelectionMode,
  removeFromSelection,
} = selectionSlice.actions;

export default selectionSlice.reducer;
