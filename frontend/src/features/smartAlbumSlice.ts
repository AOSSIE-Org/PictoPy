import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { SmartAlbum, AlbumStatistics } from '@/api/api-functions/smart_albums';

interface SmartAlbumsState {
  albums: SmartAlbum[];
  selectedAlbumId: string | null;
  statistics: AlbumStatistics | null;
  loading: boolean;
  error: string | null;
}

const initialState: SmartAlbumsState = {
  albums: [],
  selectedAlbumId: null,
  statistics: null,
  loading: false,
  error: null,
};

const smartAlbumsSlice = createSlice({
  name: 'smartAlbums',
  initialState,
  reducers: {
    // Loading states
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },

    // Albums data
    setAlbums(state, action: PayloadAction<SmartAlbum[]>) {
      state.albums = action.payload;
      state.error = null;
    },
    addAlbum(state, action: PayloadAction<SmartAlbum>) {
      state.albums.push(action.payload);
    },
    updateAlbum(state, action: PayloadAction<SmartAlbum>) {
      const index = state.albums.findIndex(
        (album) => album.album_id === action.payload.album_id
      );
      if (index !== -1) {
        state.albums[index] = action.payload;
      }
    },
    removeAlbum(state, action: PayloadAction<string>) {
      state.albums = state.albums.filter(
        (album) => album.album_id !== action.payload
      );
      if (state.selectedAlbumId === action.payload) {
        state.selectedAlbumId = null;
      }
    },

    // Selection
    setSelectedAlbumId(state, action: PayloadAction<string | null>) {
      state.selectedAlbumId = action.payload;
    },

    // Statistics
    setStatistics(state, action: PayloadAction<AlbumStatistics>) {
      state.statistics = action.payload;
    },

    // Reset
    resetSmartAlbums() {
      return initialState;
    },
  },
});

export const {
  setLoading,
  setError,
  setAlbums,
  addAlbum,
  updateAlbum,
  removeAlbum,
  setSelectedAlbumId,
  setStatistics,
  resetSmartAlbums,
} = smartAlbumsSlice.actions;

export default smartAlbumsSlice.reducer;