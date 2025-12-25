import { albumsEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';

interface CreateAlbumPayload {
  name: string;
  description?: string;
  is_hidden?: boolean;
  password?: string;
}

export interface Album {
  album_id: string;
  album_name: string;
  description: string;
  is_hidden: boolean;
}

interface GetAlbumsResponse {
  success: boolean;
  albums: Album[];
}

export const createAlbum = async (payload: CreateAlbumPayload) => {
  try {
    const response = await apiClient.post(albumsEndpoints.createAlbum, payload);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAlbums = async (): Promise<GetAlbumsResponse> => {
  try {
    const response = await apiClient.get(albumsEndpoints.getAlbums);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const addImagesToAlbum = async (albumId: string, imageIds: string[]) => {
  try {
    const response = await apiClient.post(
      albumsEndpoints.addImagesToAlbum(albumId),
      {
        image_ids: imageIds,
      },
    );
    return response.data;
  } catch (error) {
    throw error;
  }
};

interface GetAlbumImagesResponse {
  success: boolean;
  image_ids: string[];
}

export const getAlbumImages = async (
  albumId: string,
  password?: string,
): Promise<GetAlbumImagesResponse> => {
  try {
    const response = await apiClient.post(
      albumsEndpoints.getAlbumImages(albumId),
      {
        password,
      },
    );
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const removeImageFromAlbum = async (
  albumId: string,
  imageId: string,
) => {
  try {
    const response = await apiClient.delete(
      albumsEndpoints.removeImageFromAlbum(albumId, imageId),
    );
    return response.data;
  } catch (error) {
    throw error;
  }
};
