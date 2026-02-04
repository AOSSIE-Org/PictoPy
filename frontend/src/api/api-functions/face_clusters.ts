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

export interface FetchSearchedFacesRequest {
  path: string;
}

export interface FetchSearchedFacesBase64Request {
  base64_data: string;
}

export interface MergeClustersRequest {
  source_cluster_id: string;
  target_cluster_id: string;
}

export interface ToggleIgnoreRequest {
  cluster_id: string;
  is_ignored: boolean;
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

export const fetchSearchedFaces = async (
  request: FetchSearchedFacesRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    faceClustersEndpoints.searchForFaces,
    request,
  );
  return response.data;
};

export const fetchSearchedFacesBase64 = async (
  request: FetchSearchedFacesBase64Request,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    faceClustersEndpoints.searchForFacesBase64,
    request,
  );
  return response.data;
};

export const triggerGlobalReclustering = async (): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    faceClustersEndpoints.globalRecluster,
  );
  return response.data;
};

export const mergeClusters = async (
  request: MergeClustersRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    faceClustersEndpoints.mergeClusters,
    request,
  );
  return response.data;
};

export const toggleIgnoreCluster = async (
  request: ToggleIgnoreRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    faceClustersEndpoints.toggleIgnoreCluster(request.cluster_id),
    { is_ignored: request.is_ignored },
  );
  return response.data;
};
