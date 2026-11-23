import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectAlbums = (state: RootState) => state.albums.albums;
export const selectSelectedAlbum = (state: RootState) =>
  state.albums.selectedAlbum;
export const selectAlbumImages = (state: RootState) => state.albums.albumImages;

// Memoized selectors
export const selectAlbumById = createSelector(
  [selectAlbums, (_: RootState, albumId: string) => albumId],
  (albums, albumId) => albums.find((album) => album.id === albumId),
);

export const selectAlbumsCount = createSelector(
  [selectAlbums],
  (albums) => albums.length,
);

export const selectLockedAlbumsCount = createSelector(
  [selectAlbums],
  (albums) => albums.filter((album) => album.is_locked).length,
);
