import { apiClient } from '../axiosConfig';
import {
  MemoriesApiResponse,
  MemoryImagesApiResponse,
} from '@/types/memories';

export const fetchAllMemories = async (): Promise<MemoriesApiResponse> => {
  const response = await apiClient.get('/memories/');
  return response.data;
};

export const fetchMemoryImages = async (
  memoryId: string
): Promise<MemoryImagesApiResponse> => {
  const response = await apiClient.get(`/memories/${memoryId}/images`);
  return response.data;
};
