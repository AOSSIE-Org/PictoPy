import { albumsEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import {
  CreateAlbumRequest,
  UpdateAlbumRequest,
  AddImagesToAlbumRequest,
  GetAlbumImagesRequest,
  RemoveImagesFromAlbumRequest,
} from '@/types/Album';

/**
 * Get all albums
 */
export const getAllAlbums = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    albumsEndpoints.getAllAlbums,
  );
  return response.data;
};

/**
 * Get album by ID
 * @param albumId - Album UUID
 */
export const getAlbumById = async (albumId: string): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    albumsEndpoints.getAlbumById(albumId),
  );
  return response.data;
};

/**
 * Create a new album
 * @param data - Album creation data
 */
export const createAlbum = async (
  data: CreateAlbumRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    albumsEndpoints.createAlbum,
    data,
  );
  return response.data;
};

/**
 * Update an existing album
 * @param albumId - Album UUID
 * @param data - Album update data
 */
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

/**
 * Delete an album
 * @param albumId - Album UUID
 */
export const deleteAlbum = async (albumId: string): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.deleteAlbum(albumId),
  );
  return response.data;
};

/**
 * Add images to an album
 * @param albumId - Album UUID
 * @param data - Image IDs to add
 */
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

/**
 * Get all images in an album
 * @param albumId - Album UUID
 * @param data - Optional password for locked albums
 */
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

/**
 * Remove a single image from an album
 * @param albumId - Album UUID
 * @param imageId - Image UUID
 */
export const removeImageFromAlbum = async (
  albumId: string,
  imageId: string,
): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.removeImageFromAlbum(albumId, imageId),
  );
  return response.data;
};

/**
 * Remove multiple images from an album
 * @param albumId - Album UUID
 * @param data - Image IDs to remove
 */
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

/**
 * Set or update the cover image for an album
 * @param albumId - Album UUID
 * @param imageId - Image UUID to set as cover
 */
export const setAlbumCoverImage = async (
  albumId: string,
  imageId: string,
): Promise<APIResponse> => {
  const response = await apiClient.put<APIResponse>(
    albumsEndpoints.setAlbumCoverImage(albumId),
    { image_id: imageId },
  );
  return response.data;
};
