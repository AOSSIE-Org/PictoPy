import { RootState } from '@/app/store';

// Album selectors
export const selectAlbums = (state: RootState) => state.albums.albums;
export const selectSelectedAlbum = (state: RootState) => state.albums.selectedAlbum;
export const selectTotalAlbums = (state: RootState) => state.albums.totalAlbums;
export const selectAlbumsError = (state: RootState) => state.albums.error;

// Selection mode selectors
export const selectIsSelectionMode = (state: RootState) => state.albums.isSelectionMode;
export const selectSelectedImageIds = (state: RootState) => state.albums.selectedImageIds;
export const selectSelectedImageCount = (state: RootState) => state.albums.selectedImageIds.length;

// Helper selectors
export const selectIsImageSelected = (imageId: string) => (state: RootState) =>
  state.albums.selectedImageIds.includes(imageId);

export const selectHasSelectedImages = (state: RootState) =>
  state.albums.selectedImageIds.length > 0;