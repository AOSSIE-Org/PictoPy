import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllImages = async (
  tagged?: boolean,
  includeDeleted?: boolean,
): Promise<APIResponse> => {
  const params: any = {};
  if (tagged !== undefined) params.tagged = tagged;
  if (includeDeleted !== undefined) params.include_deleted = includeDeleted;
  const response = await apiClient.get<APIResponse>(
    imagesEndpoints.getAllImages,
    { params },
  );
  return response.data;
};

export const softDeleteImages = async (imageIds: string[]): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    imagesEndpoints.softDelete,
    { image_ids: imageIds },
  );
  return response.data;
};

export const restoreImages = async (imageIds: string[]): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    imagesEndpoints.restore,
    { image_ids: imageIds },
  );
  return response.data;
};

export const fetchDeletedImages = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    imagesEndpoints.getDeletedImages,
  );
  return response.data;
};


export const permanentDeleteImages = async (imageIds: string[]): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    imagesEndpoints.permanentDelete,
    { image_ids: imageIds },
  );
  return response.data;
};

export const cleanupOldImages = async (days?: number): Promise<APIResponse> => {
  const params = days !== undefined ? { days } : {};
  const response = await apiClient.post<APIResponse>(
    imagesEndpoints.cleanup,
    {},
    { params },
  );
  return response.data;
};

