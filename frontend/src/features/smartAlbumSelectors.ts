import { createSelector } from '@reduxjs/toolkit';
import type { RootState } from '@/app/store';

// Base selectors
export const selectSmartAlbumsState = (state: RootState) => state.smartAlbums;

export const selectAlbums = createSelector(
  [selectSmartAlbumsState],
  (state) => state.albums
);

export const selectSelectedAlbumId = createSelector(
  [selectSmartAlbumsState],
  (state) => state.selectedAlbumId
);

export const selectStatistics = createSelector(
  [selectSmartAlbumsState],
  (state) => state.statistics
);

export const selectLoading = createSelector(
  [selectSmartAlbumsState],
  (state) => state.loading
);

export const selectError = createSelector(
  [selectSmartAlbumsState],
  (state) => state.error
);

// Derived selectors
export const selectSelectedAlbum = createSelector(
  [selectAlbums, selectSelectedAlbumId],
  (albums, selectedId) => {
    if (!selectedId) return null;
    return albums.find((album) => album.album_id === selectedId) || null;
  }
);

export const selectObjectAlbums = createSelector(
  [selectAlbums],
  (albums) => albums.filter((album) => album.album_type === 'object')
);

export const selectFaceAlbums = createSelector(
  [selectAlbums],
  (albums) => albums.filter((album) => album.album_type === 'face')
);

export const selectAutoUpdateAlbums = createSelector(
  [selectAlbums],
  (albums) => albums.filter((album) => album.auto_update)
);

export const selectAlbumById = (albumId: string) =>
  createSelector([selectAlbums], (albums) =>
    albums.find((album) => album.album_id === albumId)
  );

export const selectAlbumsByType = (type: 'object' | 'face') =>
  createSelector([selectAlbums], (albums) =>
    albums.filter((album) => album.album_type === type)
  );

export const selectTotalImageCount = createSelector(
  [selectAlbums],
  (albums) => albums.reduce((total, album) => total + album.image_count, 0)
);