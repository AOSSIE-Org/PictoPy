import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchMemories = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getMemories,
  );
  return response.data;
};

