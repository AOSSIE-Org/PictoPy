import { faceClustersEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

//Request Types
export interface RenameClusterRequest {
  clusterId: string;
  newName: string;
}
export interface FetchClusterImagesRequest {
  clusterId: string;
}

export const fetchAllClusters = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    faceClustersEndpoints.getAllClusters,
  );
  return response.data;
};

export const renameCluster = async (
  request: RenameClusterRequest,
): Promise<APIResponse> => {
  const response = await apiClient.put<APIResponse>(
    faceClustersEndpoints.renameCluster(request.clusterId),
    { cluster_name: request.newName },
  );
  return response.data;
};

export const fetchClusterImages = async (
  request: FetchClusterImagesRequest,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    faceClustersEndpoints.getClusterImages(request.clusterId),
  );
  return response.data;
};
