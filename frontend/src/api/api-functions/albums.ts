import { albumsEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export interface Album {
  album_id: string;
  album_name: string;
  description: string;
  is_hidden: boolean;
}

export interface CreateAlbumRequest {
  name: string;
  description?: string;
  is_hidden: boolean;
  password?: string;
}

export interface UpdateAlbumRequest {
  name: string;
  description?: string;
  is_hidden: boolean;
  current_password?: string;
  password?: string;
}

export interface GetAlbumImagesRequest {
  password?: string;
}

export interface ImageIdsRequest {
  image_ids: string[];
}

export interface GetAlbumsResponse extends APIResponse {
  albums: Album[];
}

export interface CreateAlbumResponse extends APIResponse {
  album_id: string;
}

export interface GetAlbumResponse extends APIResponse {
  data: Album;
}

export interface GetAlbumImagesResponse extends APIResponse {
  image_ids: string[];
}

// Get all albums
export const fetchAllAlbums = async (showHidden = false): Promise<GetAlbumsResponse> => {
  const response = await apiClient.get<GetAlbumsResponse>(
    `${albumsEndpoints.getAllAlbums}?show_hidden=${showHidden}`,
  );
  return response.data;
};

// Create a new album
export const createAlbum = async (albumData: CreateAlbumRequest): Promise<CreateAlbumResponse> => {
  const response = await apiClient.post<CreateAlbumResponse>(
    albumsEndpoints.createAlbum,
    albumData,
  );
  return response.data;
};

// Get specific album details
export const fetchAlbum = async (albumId: string): Promise<GetAlbumResponse> => {
  const response = await apiClient.get<GetAlbumResponse>(
    albumsEndpoints.getAlbum(albumId),
  );
  return response.data;
};

// Update album
export const updateAlbum = async (
  albumId: string,
  albumData: UpdateAlbumRequest,
): Promise<APIResponse> => {
  const response = await apiClient.put<APIResponse>(
    albumsEndpoints.updateAlbum(albumId),
    albumData,
  );
  return response.data;
};

// Delete album
export const deleteAlbum = async (albumId: string): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.deleteAlbum(albumId),
  );
  return response.data;
};

// Get album images
export const fetchAlbumImages = async (
  albumId: string,
  password?: string,
): Promise<GetAlbumImagesResponse> => {
  const requestBody: GetAlbumImagesRequest = {};
  if (password) {
    requestBody.password = password;
  }

  const response = await apiClient.post<GetAlbumImagesResponse>(
    albumsEndpoints.getAlbumImages(albumId),
    requestBody,
  );
  return response.data;
};

// Add images to album
export const addImagesToAlbum = async (
  albumId: string,
  imageIds: string[],
): Promise<APIResponse> => {
  const requestBody: ImageIdsRequest = { image_ids: imageIds };
  const response = await apiClient.post<APIResponse>(
    albumsEndpoints.addImagesToAlbum(albumId),
    requestBody,
  );
  return response.data;
};

// Remove image from album
export const removeImageFromAlbum = async (
  albumId: string,
  imageId: string,
): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.removeImageFromAlbum(albumId, imageId),
  );
  return response.data;
};

// Remove multiple images from album
export const removeImagesFromAlbum = async (
  albumId: string,
  imageIds: string[],
): Promise<APIResponse> => {
  const requestBody: ImageIdsRequest = { image_ids: imageIds };
  const response = await apiClient.delete<APIResponse>(
    albumsEndpoints.removeImagesFromAlbum(albumId),
    { data: requestBody },
  );
  return response.data;
};