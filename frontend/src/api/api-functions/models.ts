import { apiClient } from '../axiosConfig';
import { ModelStatusResponse, HardwareResponse } from '@/types/models';
import { APIResponse } from '@/types/API';

export const fetchModelStatus = async (): Promise<ModelStatusResponse> => {
  const response = await apiClient.get<ModelStatusResponse>('/models/status');
  return response.data;
};

export const fetchHardwareInfo = async (): Promise<HardwareResponse> => {
  const response = await apiClient.get<HardwareResponse>('/models/hardware');
  return response.data;
};

export const setupModelTier = async (
  tier: string,
): Promise<APIResponse & { task_id?: string }> => {
  const response = await apiClient.post<APIResponse & { task_id?: string }>(
    '/models/setup',
    { tier },
  );
  return response.data;
};

export const deleteModel = async (modelKey: string): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(`/models/${modelKey}`);
  return response.data;
};
