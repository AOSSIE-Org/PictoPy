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
