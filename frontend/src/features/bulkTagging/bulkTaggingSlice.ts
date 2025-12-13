import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface BulkTaggingState {
  selectedFolderIds: string[];
  isProcessing: boolean;
  lastError: string | null;
}

const initialState: BulkTaggingState = {
  selectedFolderIds: [],
  isProcessing: false,
  lastError: null,
};

const bulkTaggingSlice = createSlice({
  name: 'bulkTagging',
  initialState,
  reducers: {
    toggleFolderSelection: (state, action: PayloadAction<string>) => {
      const folderId = action.payload;
      const index = state.selectedFolderIds.indexOf(folderId);
      if (index > -1) {
        state.selectedFolderIds.splice(index, 1);
      } else {
        state.selectedFolderIds.push(folderId);
      }
    },
    selectAllFolders: (state, action: PayloadAction<string[]>) => {
      state.selectedFolderIds = action.payload;
    },
    deselectAllFolders: (state) => {
      state.selectedFolderIds = [];
    },
    setProcessing: (state, action: PayloadAction<boolean>) => {
      state.isProcessing = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.lastError = action.payload;
    },
    clearSelections: (state) => {
      state.selectedFolderIds = [];
      state.lastError = null;
    },
  },
});

export const {
  toggleFolderSelection,
  selectAllFolders,
  deselectAllFolders,
  setProcessing,
  setError,
  clearSelections,
} = bulkTaggingSlice.actions;

export default bulkTaggingSlice.reducer;
