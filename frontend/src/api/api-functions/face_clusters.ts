import { faceClustersEndpoints } from '../apiEndpoints';
import { apiClient, LONG_REQUEST_TIMEOUT_MS } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { BackendRes } from '@/hooks/useQueryExtension';
import type { Image } from '@/types/Media';

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
    { timeout: LONG_REQUEST_TIMEOUT_MS },
  );
  return response.data;
};

export const fetchSearchedFacesBase64 = async (
  request: FetchSearchedFacesBase64Request,
): Promise<BackendRes<Image[]>> => {
  const response = await apiClient.post<BackendRes<Image[]>>(
    faceClustersEndpoints.searchForFacesBase64,
    request,
    { timeout: LONG_REQUEST_TIMEOUT_MS },
  );
  return response.data;
};

export interface GlobalReclusterData {
  clusters_created: number | null;
  faces_skipped: number | null;
}

export interface GlobalReclusterStartData {
  task_id: string;
}

export interface GlobalReclusterStatusData {
  status: 'running' | 'complete' | 'error';
  clusters_created: number | null;
  faces_skipped: number | null;
}

// Global reclustering runs over every face embedding in the library and can
// take well past any reasonable HTTP timeout, so the backend runs it as a
// background job: this kicks it off and returns a task_id immediately.
export const startGlobalReclustering = async (): Promise<
  BackendRes<GlobalReclusterStartData>
> => {
  const response = await apiClient.post<BackendRes<GlobalReclusterStartData>>(
    faceClustersEndpoints.globalRecluster,
  );
  return response.data;
};

// Poll this with the task_id returned by startGlobalReclustering until
// status is 'complete' or 'error'.
export const getGlobalReclusterStatus = async (
  taskId: string,
): Promise<BackendRes<GlobalReclusterStatusData>> => {
  const response = await apiClient.get<BackendRes<GlobalReclusterStatusData>>(
    faceClustersEndpoints.globalReclusterStatus(taskId),
  );
  return response.data;
};

export interface MultiPersonSearchRequest {
  cluster_ids: string[];
  match_mode: 'match_any' | 'match_all';
}

export const fetchMultiPersonSearch = async (
  request: MultiPersonSearchRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    faceClustersEndpoints.multiPersonSearch,
    request,
    { timeout: LONG_REQUEST_TIMEOUT_MS },
  );
  return response.data;
};
