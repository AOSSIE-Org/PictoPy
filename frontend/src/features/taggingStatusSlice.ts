import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { FolderTaggingInfo } from '@/types/FolderStatus';

interface TaggingStatusState {
  byFolderId: Record<string, FolderTaggingInfo>;
  lastUpdatedAt?: number;
}

const initialState: TaggingStatusState = {
  byFolderId: {},
};

const taggingStatusSlice = createSlice({
  name: 'taggingStatus',
  initialState,
  reducers: {
    setTaggingStatus(
      state,
      action: PayloadAction<FolderTaggingInfo[]>,
    ) {
      const map: Record<string, FolderTaggingInfo> = {};
      for (const info of action.payload) {
        map[info.folder_id] = info;
      }
      state.byFolderId = map;
      state.lastUpdatedAt = Date.now();
    },
    clearTaggingStatus(state) {
      state.byFolderId = {};
      state.lastUpdatedAt = undefined;
    },
  },
});

export const { setTaggingStatus, clearTaggingStatus } = taggingStatusSlice.actions;
export default taggingStatusSlice.reducer;



