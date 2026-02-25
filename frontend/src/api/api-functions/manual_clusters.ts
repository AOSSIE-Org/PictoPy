import { manualClustersEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import {
  AssignImagesPayload,
  CreateClusterPayload,
  RenameClusterPayload,
} from '@/types/ManualCluster';

export const fetchAllManualClusters = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    manualClustersEndpoints.getAll,
  );
  return response.data;
};

export const fetchManualClusterById = async (
  clusterId: string,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    manualClustersEndpoints.getById(clusterId),
  );
  return response.data;
};

export const createManualCluster = async (
  payload: CreateClusterPayload,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    manualClustersEndpoints.create,
    payload,
  );
  return response.data;
};

export const renameManualCluster = async (
  clusterId: string,
  payload: RenameClusterPayload,
): Promise<APIResponse> => {
  const response = await apiClient.patch<APIResponse>(
    manualClustersEndpoints.rename(clusterId),
    payload,
  );
  return response.data;
};

export const deleteManualCluster = async (
  clusterId: string,
): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    manualClustersEndpoints.delete(clusterId),
  );
  return response.data;
};

export const assignImagesToCluster = async (
  clusterId: string,
  payload: AssignImagesPayload,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    manualClustersEndpoints.assignImages(clusterId),
    payload,
  );
  return response.data;
};

export const removeImageFromCluster = async (
  clusterId: string,
  imageId: string,
): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    manualClustersEndpoints.removeImage(clusterId, imageId),
  );
  return response.data;
};
