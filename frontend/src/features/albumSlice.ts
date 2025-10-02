import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Album {
  album_id: string;
  album_name: string;
  description: string;
  is_hidden: boolean;
}

interface AlbumState {
  albums: Album[];
  selectedAlbum: Album | null;
  selectedImageIds: string[];
  isSelectionMode: boolean;
  totalAlbums: number;
  error: string | null;
}

const initialState: AlbumState = {
  albums: [],
  selectedAlbum: null,
  selectedImageIds: [],
  isSelectionMode: false,
  totalAlbums: 0,
  error: null,
};

const albumSlice = createSlice({
  name: 'albums',
  initialState,
  reducers: {
    setAlbums(state, action: PayloadAction<Album[]>) {
      state.albums = action.payload;
      state.totalAlbums = action.payload.length;
      state.error = null;
    },
    addAlbum(state, action: PayloadAction<Album>) {
      state.albums.push(action.payload);
      state.totalAlbums = state.albums.length;
    },
    updateAlbum(
      state,
      action: PayloadAction<{ albumId: string; updates: Partial<Album> }>,
    ) {
      const { albumId, updates } = action.payload;
      const albumIndex = state.albums.findIndex(
        (album) => album.album_id === albumId,
      );
      if (albumIndex !== -1) {
        state.albums[albumIndex] = { ...state.albums[albumIndex], ...updates };
        if (state.selectedAlbum?.album_id === albumId) {
          state.selectedAlbum = { ...state.selectedAlbum, ...updates };
        }
      }
    },
    removeAlbum(state, action: PayloadAction<string>) {
      const albumId = action.payload;
      const albumIndex = state.albums.findIndex(
        (album) => album.album_id === albumId,
      );
      if (albumIndex !== -1) {
        state.albums.splice(albumIndex, 1);
        state.totalAlbums = state.albums.length;
      }
      // Clear selected album if it was deleted
      if (state.selectedAlbum?.album_id === albumId) {
        state.selectedAlbum = null;
      }
    },
    setSelectedAlbum(state, action: PayloadAction<Album | null>) {
      state.selectedAlbum = action.payload;
    },
    // Selection mode actions
    enableSelectionMode(state) {
      state.isSelectionMode = true;
    },
    disableSelectionMode(state) {
      state.isSelectionMode = false;
      state.selectedImageIds = [];
    },
    toggleImageSelection(state, action: PayloadAction<string>) {
      const imageId = action.payload;
      const index = state.selectedImageIds.indexOf(imageId);
      if (index === -1) {
        state.selectedImageIds.push(imageId);
      } else {
        state.selectedImageIds.splice(index, 1);
      }
    },
    selectImage(state, action: PayloadAction<string>) {
      const imageId = action.payload;
      if (!state.selectedImageIds.includes(imageId)) {
        state.selectedImageIds.push(imageId);
      }
    },
    deselectImage(state, action: PayloadAction<string>) {
      const imageId = action.payload;
      const index = state.selectedImageIds.indexOf(imageId);
      if (index !== -1) {
        state.selectedImageIds.splice(index, 1);
      }
    },
    selectAllImages(state, action: PayloadAction<string[]>) {
      state.selectedImageIds = action.payload;
    },
    clearSelectedImages(state) {
      state.selectedImageIds = [];
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    clearError(state) {
      state.error = null;
    },
  },
});

export const {
  setAlbums,
  addAlbum,
  updateAlbum,
  removeAlbum,
  setSelectedAlbum,
  enableSelectionMode,
  disableSelectionMode,
  toggleImageSelection,
  selectImage,
  deselectImage,
  selectAllImages,
  clearSelectedImages,
  setError,
  clearError,
} = albumSlice.actions;

export default albumSlice.reducer;
