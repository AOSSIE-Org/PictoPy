import { videosEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export interface VideoData {
  id: string;
  path: string;
  folder_id: string;
  thumbnailPath: string;
  duration?: number;
  width?: number;
  height?: number;
  isFavourite: boolean;
  metadata?: {
    name: string;
    file_location: string;
    file_size: number;
    duration?: number;
    width?: number;
    height?: number;
    codec?: string;
    date_created?: string;
  };
}

export interface GetAllVideosResponse extends APIResponse {
  data: VideoData[];
}

export const fetchAllVideos = async (): Promise<GetAllVideosResponse> => {
  const response = await apiClient.get<GetAllVideosResponse>(
    videosEndpoints.getAllVideos,
  );
  return response.data;
};

export const fetchVideoById = async (videoId: string): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    videosEndpoints.getVideo(videoId),
  );
  return response.data;
};

export const toggleVideoFavourite = async (videoId: string): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    videosEndpoints.toggleFavourite,
    { video_id: videoId },
  );
  return response.data;
};
