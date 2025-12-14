// src/api/api-functions/memories.ts

import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import {
  GenerateMemoriesRequest,
  GenerateMemoriesResponse,
  MemoryDetail,
  MemorySummary,
} from '@/types/Memory';

// Response types
interface GetAllMemoriesResponse extends APIResponse {
  data: MemorySummary[];
}

interface GetMemoryDetailResponse extends APIResponse {
  data: MemoryDetail;
}

// API Functions
export const getAllMemories = async (): Promise<GetAllMemoriesResponse> => {
  const response = await apiClient.get<GetAllMemoriesResponse>(
    memoriesEndpoints.getAllMemories,
  );
  return response.data;
};

export const getMemoryDetail = async (
  memoryId: string,
): Promise<GetMemoryDetailResponse> => {
  const response = await apiClient.get<GetMemoryDetailResponse>(
    memoriesEndpoints.getMemoryDetail(memoryId),
  );
  return response.data;
};

export const generateMemories = async (
  request: GenerateMemoriesRequest = {},
): Promise<GenerateMemoriesResponse> => {
  const response = await apiClient.post<GenerateMemoriesResponse>(
    memoriesEndpoints.generateMemories,
    request,
  );
  return response.data;
};

export const deleteMemory = async (memoryId: string): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    memoriesEndpoints.deleteMemory(memoryId),
  );
  return response.data;
};