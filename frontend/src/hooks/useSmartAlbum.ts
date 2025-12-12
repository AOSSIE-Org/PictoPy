import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch } from '@/app/store';
import {
  fetchSmartAlbums,
  createObjectAlbumThunk,
  createFaceAlbumThunk,
  createPredefinedAlbumsThunk,
  refreshAlbumThunk,
  refreshAllAlbumsThunk,
  updateAlbumThunk,
  deleteAlbumThunk,
  fetchStatistics,
} from '@/features/smartAlbumThunk';
import {
  selectAlbums,
  selectSelectedAlbum,
  selectStatistics,
  selectLoading,
  selectError,
} from '@/features/smartAlbumSelectors';
import { setSelectedAlbumId } from '@/features/smartAlbumSlice';
import type {
  CreateObjectAlbumRequest,
  CreateFaceAlbumRequest,
  UpdateAlbumRequest,
} from '@/api/api-functions/smart_albums';


export const useSmartAlbums = () => {
  const dispatch = useDispatch<AppDispatch>();

  // Selectors
  const albums = useSelector(selectAlbums);
  const selectedAlbum = useSelector(selectSelectedAlbum);
  const statistics = useSelector(selectStatistics);
  const loading = useSelector(selectLoading);
  const error = useSelector(selectError);

  // Actions
  const fetchAlbums = useCallback(() => {
    dispatch(fetchSmartAlbums());
  }, [dispatch]);

  const createObjectAlbum = useCallback(
    (request: CreateObjectAlbumRequest) => {
      return dispatch(createObjectAlbumThunk(request)).unwrap();
    },
    [dispatch]
  );

  const createFaceAlbum = useCallback(
    (request: CreateFaceAlbumRequest) => {
      return dispatch(createFaceAlbumThunk(request)).unwrap();
    },
    [dispatch]
  );

  const createPredefinedAlbums = useCallback(() => {
    return dispatch(createPredefinedAlbumsThunk()).unwrap();
  }, [dispatch]);

  const refreshAlbum = useCallback(
    (albumId: string) => {
      return dispatch(refreshAlbumThunk(albumId)).unwrap();
    },
    [dispatch]
  );

  const refreshAllAlbums = useCallback(() => {
    return dispatch(refreshAllAlbumsThunk()).unwrap();
  }, [dispatch]);

  const updateAlbum = useCallback(
    (albumId: string, request: UpdateAlbumRequest) => {
      return dispatch(updateAlbumThunk({ albumId, request })).unwrap();
    },
    [dispatch]
  );

  const deleteAlbum = useCallback(
    (albumId: string) => {
      return dispatch(deleteAlbumThunk(albumId)).unwrap();
    },
    [dispatch]
  );

  const selectAlbum = useCallback(
    (albumId: string | null) => {
      dispatch(setSelectedAlbumId(albumId));
    },
    [dispatch]
  );

  const loadStatistics = useCallback(() => {
    dispatch(fetchStatistics());
  }, [dispatch]);

  return {
    // Data
    albums,
    selectedAlbum,
    statistics,
    loading,
    error,

    // Actions
    fetchAlbums,
    createObjectAlbum,
    createFaceAlbum,
    createPredefinedAlbums,
    refreshAlbum,
    refreshAllAlbums,
    updateAlbum,
    deleteAlbum,
    selectAlbum,
    loadStatistics,
  };
};