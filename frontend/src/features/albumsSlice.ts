import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Album } from '@/types/Album';
import { Image } from '@/types/Media';

interface AlbumsState {
  albums: Album[];
  selectedAlbum: Album | null;
  albumImages: Image[];
}

const initialState: AlbumsState = {
  albums: [],
  selectedAlbum: null,
  albumImages: [],
};

const albumsSlice = createSlice({
  name: 'albums',
  initialState,
  reducers: {
    setAlbums(state, action: PayloadAction<Album[]>) {
      state.albums = action.payload;
    },

    addAlbum(state, action: PayloadAction<Album>) {
      state.albums.push(action.payload);
    },

    updateAlbumInList(state, action: PayloadAction<Album>) {
      const index = state.albums.findIndex(
        (album) => album.id === action.payload.id,
      );
      if (index !== -1) {
        state.albums[index] = action.payload;
      }
    },

    removeAlbum(state, action: PayloadAction<string>) {
      state.albums = state.albums.filter(
        (album) => album.id !== action.payload,
      );
      if (state.selectedAlbum?.id === action.payload) {
        state.selectedAlbum = null;
        state.albumImages = [];
      }
    },

    setSelectedAlbum(state, action: PayloadAction<Album | null>) {
      state.selectedAlbum = action.payload;
    },

    setAlbumImages(state, action: PayloadAction<Image[]>) {
      state.albumImages = action.payload;
    },

    addImageToAlbum(state, action: PayloadAction<Image>) {
      state.albumImages.push(action.payload);
      if (state.selectedAlbum) {
        state.selectedAlbum.image_count += 1;
      }
    },

    removeImageFromAlbumState(state, action: PayloadAction<string>) {
      state.albumImages = state.albumImages.filter(
        (image) => image.id !== action.payload,
      );
      if (state.selectedAlbum && state.selectedAlbum.image_count > 0) {
        state.selectedAlbum.image_count -= 1;
      }
    },

    clearAlbumImages(state) {
      state.albumImages = [];
    },

    clearAlbums(state) {
      state.albums = [];
      state.selectedAlbum = null;
      state.albumImages = [];
    },
  },
});

export const {
  setAlbums,
  addAlbum,
  updateAlbumInList,
  removeAlbum,
  setSelectedAlbum,
  setAlbumImages,
  addImageToAlbum,
  removeImageFromAlbumState,
  clearAlbumImages,
  clearAlbums,
} = albumsSlice.actions;

export default albumsSlice.reducer;
