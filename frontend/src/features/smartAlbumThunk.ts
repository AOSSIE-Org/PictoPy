import { createAsyncThunk } from '@reduxjs/toolkit';
import {
  getAllSmartAlbums,
  createObjectAlbum,
  createFaceAlbum,
  createPredefinedAlbums,
  refreshAlbum,
  refreshAllAlbums,
  updateAlbum,
  deleteAlbum,
  getAlbumStatistics,
  type CreateObjectAlbumRequest,
  type CreateFaceAlbumRequest,
  type UpdateAlbumRequest,
} from '@/api/api-functions/smart_albums';
import { setLoading,setError,setAlbums,addAlbum,updateAlbum as updateAlbumAction,setStatistics, removeAlbum } from "./smartAlbumSlice";


/**
 * Fetch all smart albums
 */
export const fetchSmartAlbums = createAsyncThunk(
  'smartAlbums/fetchAll',
  async (_, { dispatch, rejectWithValue }) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const albums = await getAllSmartAlbums();
      dispatch(setAlbums(albums));
      return albums;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch albums';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Create object-based smart album
 */
export const createObjectAlbumThunk = createAsyncThunk(
  'smartAlbums/createObject',
  async (request: CreateObjectAlbumRequest, { dispatch, rejectWithValue }) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const newAlbum = await createObjectAlbum(request);
      dispatch(addAlbum(newAlbum));
      // Refresh statistics
      dispatch(fetchStatistics());
      return newAlbum;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create album';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Create face-based smart album
 */
export const createFaceAlbumThunk = createAsyncThunk(
  'smartAlbums/createFace',
  async (request: CreateFaceAlbumRequest, { dispatch, rejectWithValue }) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const newAlbum = await createFaceAlbum(request);
      dispatch(addAlbum(newAlbum));
      dispatch(fetchStatistics());
      return newAlbum;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create face album';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Create predefined albums
 */
export const createPredefinedAlbumsThunk = createAsyncThunk(
  'smartAlbums/createPredefined',
  async (_, { dispatch, rejectWithValue }) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const result = await createPredefinedAlbums();
      // Refresh albums list
      dispatch(fetchSmartAlbums());
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create predefined albums';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Refresh single album
 */
export const refreshAlbumThunk = createAsyncThunk(
  'smartAlbums/refresh',
  async (albumId: string, { dispatch, rejectWithValue }) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const result = await refreshAlbum(albumId);
      dispatch(updateAlbumAction(result.album));
      dispatch(fetchStatistics());
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to refresh album';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Refresh all albums
 */
export const refreshAllAlbumsThunk = createAsyncThunk(
  'smartAlbums/refreshAll',
  async (_, { dispatch, rejectWithValue }) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const result = await refreshAllAlbums();
      dispatch(setAlbums(result.albums));
      dispatch(fetchStatistics());
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to refresh all albums';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Update album
 */
export const updateAlbumThunk = createAsyncThunk(
  'smartAlbums/update',
  async (
    { albumId, request }: { albumId: string; request: UpdateAlbumRequest },
    { dispatch, rejectWithValue }
  ) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const updatedAlbum = await updateAlbum(albumId, request);
      dispatch(updateAlbumAction(updatedAlbum));
      return updatedAlbum;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update album';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Delete album
 */
export const deleteAlbumThunk = createAsyncThunk(
  'smartAlbums/delete',
  async (albumId: string, { dispatch, rejectWithValue }) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
    try {
      const result = await deleteAlbum(albumId);
      dispatch(removeAlbum(albumId));
      dispatch(fetchStatistics());
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete album';
      dispatch(setError(message));
      return rejectWithValue(message);
    } finally {
      dispatch(setLoading(false));
    }
  }
);

/**
 * Fetch statistics
 */
export const fetchStatistics = createAsyncThunk(
  'smartAlbums/fetchStatistics',
  async (_, { dispatch, rejectWithValue }) => {
    try {
      const statistics = await getAlbumStatistics();
      dispatch(setStatistics(statistics));
      return statistics;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch statistics';
      return rejectWithValue(message);
    }
  }
);