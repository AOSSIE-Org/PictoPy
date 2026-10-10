import { albumsEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import type { BackendRes } from '@/hooks/useQueryExtension';
import {
  CreateAlbumRequest,
  CreateAlbumFromMemoryData,
  CreateAlbumFromMemoryRequest,
  UpdateAlbumRequest,
  AddImagesToAlbumRequest,
  GetAlbumImagesRequest,
  RemoveImagesFromAlbumRequest,
} from '@/types/Album';

export const getAllAlbums = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    albumsEndpoints.getAllAlbums,
  );
  return response.data;
};

export const getAlbumById = async (albumId: string): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    albumsEndpoints.getAlbumById(albumId),
  );
  return response.data;
};

export const createAlbum = async (
  data: CreateAlbumRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    albumsEndpoints.createAlbum,
    data,
  );
  return response.data;
};

export const createAlbumFromMemory = async (
  data: CreateAlbumFromMemoryRequest,
): Promise<BackendRes<CreateAlbumFromMemoryData>> => {
  const response = await apiClient.post(
    albumsEndpoints.createAlbumFromMemory,
    data,
  );
  return response.data;
};

export const updateAlbum = async (
  albumId: string,
  data: UpdateAlbumRequest,
): Promise<APIResponse> => {
  const response = await apiClient.put<APIResponse>(
    albumsEndpoints.updateAlbum(albumId),
    data,
  );
  return response.data;
};

export const deleteAlbum = async (albumId: string): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.deleteAlbum(albumId),
  );
  return response.data;
};

export const addImagesToAlbum = async (
  albumId: string,
  data: AddImagesToAlbumRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    albumsEndpoints.addImagesToAlbum(albumId),
    data,
  );
  return response.data;
};

// Reads use POST so a locked album's password stays out of the URL.
export const getAlbumImages = async (
  albumId: string,
  data?: GetAlbumImagesRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    albumsEndpoints.getAlbumImages(albumId),
    data || {},
  );
  return response.data;
};

export const removeImageFromAlbum = async (
  albumId: string,
  imageId: string,
): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.removeImageFromAlbum(albumId, imageId),
  );
  return response.data;
};

export const removeMultipleImagesFromAlbum = async (
  albumId: string,
  data: RemoveImagesFromAlbumRequest,
): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.removeMultipleImagesFromAlbum(albumId),
    { data },
  );
  return response.data;
};
