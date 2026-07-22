import { videosEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllVideos = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    videosEndpoints.getAllVideos,
  );
  return response.data;
};

export const toggleVideoFav = async (
  video_id: string,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    videosEndpoints.setFavourite,
    { video_id },
  );
  return response.data;
};
