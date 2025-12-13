import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllMemories = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getAllMemories,
  );
  return response.data;
};

export interface FetchMemoryImagesRequest {
  memoryId: string;
}

export const fetchMemoryImages = async (
  request: FetchMemoryImagesRequest,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.getMemoryImages(request.memoryId),
  );
  return response.data;
};

export const generateMemories = async (): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    memoriesEndpoints.generateMemories,
  );
  return response.data;
};
