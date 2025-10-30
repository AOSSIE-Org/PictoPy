import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { MemoriesResponse } from '@/types/Memory';

export const fetchAllMemories = async (params?: {
  years_back?: number;
  recent_days?: number;
  min_images?: number;
  people_limit?: number;
  tags_limit?: number;
}): Promise<MemoriesResponse> => {
  const response = await apiClient.get<MemoriesResponse>(
    memoriesEndpoints.getAllMemories,
    { params },
  );
  return response.data;
};

export const fetchOnThisDayMemories = async (
  years_back: number = 5,
): Promise<any> => {
  const response = await apiClient.get(memoriesEndpoints.onThisDay, {
    params: { years_back },
  });
  return response.data;
};

export const fetchRecentMemories = async (
  days: number = 30,
  min_images: number = 5,
): Promise<any> => {
  const response = await apiClient.get(memoriesEndpoints.recent, {
    params: { days, min_images },
  });
  return response.data;
};

export const fetchPeopleMemories = async (limit: number = 10): Promise<any> => {
  const response = await apiClient.get(memoriesEndpoints.people, {
    params: { limit },
  });
  return response.data;
};

export const fetchTagMemories = async (limit: number = 10): Promise<any> => {
  const response = await apiClient.get(memoriesEndpoints.tags, {
    params: { limit },
  });
  return response.data;
};
