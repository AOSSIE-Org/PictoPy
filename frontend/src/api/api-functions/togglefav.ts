import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const togglefav = async (image_id: number): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    imagesEndpoints.setFavourite,
    { image_id: image_id.toString() },
  );
  return response.data;
};
