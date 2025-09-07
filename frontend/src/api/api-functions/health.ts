import { healthEndpoints } from '../apiEndpoints';
import { apiClient, syncApiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
export const getMainBackendHealthStatus = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    healthEndpoints.healthCheck,
  );
  return response.data;
};
export const getSyncMicroserviceHealthStatus =
  async (): Promise<APIResponse> => {
    const response = await syncApiClient.get<APIResponse>(
      healthEndpoints.healthCheck,
    );
    return response.data;
  };
