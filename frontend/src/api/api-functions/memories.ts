import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllMemories = async (
  limit?: number,
): Promise<APIResponse> => {
  const params = limit !== undefined ? { limit } : {};
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getAllMemories,
    { params },
  );
  return response.data;
};

export const fetchMemoryById = async (
  memoryId: string,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getMemoryById(memoryId),
  );
  return response.data;
};
