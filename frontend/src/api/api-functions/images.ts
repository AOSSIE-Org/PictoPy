import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllImages = async (
  tagged?: boolean,
): Promise<APIResponse> => {
  const params = tagged !== undefined ? { tagged } : {};
  const response = await apiClient.get<APIResponse>(
    imagesEndpoints.getAllImages,
    { params },
  );
  return response.data;
};

export const renameImage = async (
  imageId: string,
  newName: string,
): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.put(imagesEndpoints.renameImage, {
    image_id: imageId,
    rename: newName,
  });
  return response.data;
};
