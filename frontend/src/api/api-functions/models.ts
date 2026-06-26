import { apiClient } from '../axiosConfig';
import { ModelStatusResponse } from '@/types/models';
import { APIResponse } from '@/types/API';

export const fetchModelStatus = async (): Promise<ModelStatusResponse> => {
  const response = await apiClient.get<ModelStatusResponse>('/models/status');
  return response.data;
};

export const deleteModel = async (modelKey: string): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(`/models/${modelKey}`);
  return response.data;
};
