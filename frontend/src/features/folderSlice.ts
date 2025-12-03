import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { FolderDetails } from '@/types/Folder';
import { FolderTaggingInfo } from '@/types/FolderStatus';

interface FolderState {
  folders: FolderDetails[];
  taggingStatus: Record<string, FolderTaggingInfo>;
  folderStatusTimestamps: Record<string, number>; 
  lastUpdatedAt?: number;
}

const initialState: FolderState = {
  folders: [],
  taggingStatus: {},
  folderStatusTimestamps: {}, 
};

const folderSlice = createSlice({
  name: 'folders',
  initialState,
  reducers: {
    // Set all folders
    setFolders(state, action: PayloadAction<FolderDetails[]>) {
      state.folders = action.payload;
    },

    // Add a single folder
    addFolder(state, action: PayloadAction<FolderDetails>) {
      const newFolder = action.payload;
      const existingIndex = state.folders.findIndex(
        (folder) => folder.folder_id === newFolder.folder_id,
      );

      if (existingIndex === -1) {
        state.folders.push(newFolder);
      } else {
        // Update existing folder
        state.folders[existingIndex] = newFolder;
      }
    },

    // Update an existing folder
    updateFolder(
      state,
      action: PayloadAction<{
        folderId: string;
        updates: Partial<FolderDetails>;
      }>,
    ) {
      const { folderId, updates } = action.payload;
      const folderIndex = state.folders.findIndex(
        (folder) => folder.folder_id === folderId,
      );

      if (folderIndex !== -1) {
        state.folders[folderIndex] = {
          ...state.folders[folderIndex],
          ...updates,
        };
      }
    },

    // Remove folders by IDs
    removeFolders(state, action: PayloadAction<string[]>) {
      const folderIdsToRemove = action.payload;
      state.folders = state.folders.filter(
        (folder) => !folderIdsToRemove.includes(folder.folder_id),
      );
    },

    // Clear all folder data
    clearFolders(state) {
      state.folders = [];
    },

    // Set tagging status for folders
  setTaggingStatus(state, action: PayloadAction<FolderTaggingInfo[]>) {
  const map: Record<string, FolderTaggingInfo> = {};
  const now = Date.now();
  const currentFolderIds = new Set<string>();
  
  for (const info of action.payload) {
    map[info.folder_id] = info;
    currentFolderIds.add(info.folder_id);
    const existingStatus = state.taggingStatus[info.folder_id];
    if (
      !existingStatus ||
      existingStatus.total_images !== info.total_images ||
      existingStatus.tagged_images !== info.tagged_images
    ) {
      state.folderStatusTimestamps[info.folder_id] = now;
    }
  }
  
  for (const folderId in state.folderStatusTimestamps) {
    if (!currentFolderIds.has(folderId)) {
      delete state.folderStatusTimestamps[folderId];
    }
  }
  
  state.taggingStatus = map;
  state.lastUpdatedAt = now;
},

    // Clear tagging status
    clearTaggingStatus(state) {
      state.taggingStatus = {};
      state.folderStatusTimestamps = {};
      state.lastUpdatedAt = undefined;
    },
  },
});

export const {
  setFolders,
  addFolder,
  updateFolder,
  removeFolders,
  clearFolders,
  setTaggingStatus,
  clearTaggingStatus,
} = folderSlice.actions;

export default folderSlice.reducer;
