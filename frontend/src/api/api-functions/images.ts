import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllImages = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    imagesEndpoints.getAllImages,
  );
  return response.data;
};
