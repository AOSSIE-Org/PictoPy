import { videosEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { ScoredVideo } from '@/types/Media';

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

export interface SearchVideosByTagRequest {
  tag: string;
}

export const searchVideosByTag = async (
  request: SearchVideosByTagRequest,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    videosEndpoints.searchByTag(request.tag),
  );
  return response.data;
};

export interface SemanticSearchVideosRequest {
  query: string;
}

export interface SemanticSearchVideosAPIResponse extends APIResponse {
  data?: {
    videos: ScoredVideo[];
    total: number;
  };
}

export const semanticSearchVideos = async (
  request: SemanticSearchVideosRequest,
): Promise<SemanticSearchVideosAPIResponse> => {
  const response = await apiClient.get<SemanticSearchVideosAPIResponse>(
    videosEndpoints.semanticSearch(request.query),
  );
  return response.data;
};

export interface PurgeFrameCacheResponse {
  success: boolean;
  message: string;
  bytes_reclaimed: number;
}

export const purgeVideoFrameCache =
  async (): Promise<PurgeFrameCacheResponse> => {
    const response = await apiClient.post<PurgeFrameCacheResponse>(
      videosEndpoints.purgeFrameCache,
    );
    return response.data;
  };
