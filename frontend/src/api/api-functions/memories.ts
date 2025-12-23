import { apiClient } from '../axiosConfig';
import { memoriesEndpoints } from '../apiEndpoints';
import { APIResponse } from '@/types/API';

export const fetchMemories = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getAllMemories,
  );
  return response.data;
};
