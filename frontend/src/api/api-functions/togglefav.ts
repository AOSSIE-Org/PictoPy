import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const togglefav = async (image_id: string): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    imagesEndpoints.setFavourite,
    { image_id },
  );
  return response.data;
};
