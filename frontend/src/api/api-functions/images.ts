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


export const searchImages = async (query: string, tagged?: boolean): Promise<any> => {
  const params = new URLSearchParams({ query });
  if (tagged !== undefined) {
    params.append('tagged', tagged.toString());
  }
  const response = await apiClient.get(`/images/search?${params.toString()}`);
  return response.data;
};
