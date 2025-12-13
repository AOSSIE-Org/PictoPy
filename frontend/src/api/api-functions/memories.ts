import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllMemories = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getAllMemories,
  );
  return response.data;
};

export const fetchTodayMemories = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getTodayMemories,
  );
  return response.data;
};

export const fetchMemoryImages = async (
  memoryId: string,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getMemoryImages(memoryId),
  );
  return response.data;
};
