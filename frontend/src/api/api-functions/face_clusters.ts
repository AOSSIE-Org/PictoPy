import { faceClustersEndpoints } from '../apiEndpoints';
import { apiClient, LONG_REQUEST_TIMEOUT_MS } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { BackendRes } from '@/hooks/useQueryExtension';
import type { Image, ImageMetadata, Video } from '@/types/Media';

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

//Response Types
/** A photo as the face routes return it: less than a full `Image`. */
export interface FacePhoto {
  id: string;
  path: string;
  thumbnailPath?: string | null;
  metadata?: ImageMetadata | null;
}

export interface ClusterImage extends FacePhoto {
  face_id: number;
  confidence?: number | null;
  bbox?: Record<string, number> | null;
}

export interface ClusterImagesData {
  cluster_id: string;
  cluster_name: string | null;
  images: ClusterImage[];
  total_images: number;
  videos: Video[];
  total_videos: number;
}

/** Face search puts its videos beside `data`, not inside it. */
export interface FaceSearchResponse extends BackendRes<Image[]> {
  videos?: Video[];
}

export interface MultiPersonSearchData {
  images: (FacePhoto & { match_count: number })[];
  total: number;
  match_mode: MultiPersonSearchRequest['match_mode'];
  videos: (Video & { match_count: number })[];
  total_videos: number;
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
): Promise<BackendRes<ClusterImagesData>> => {
  const response = await apiClient.get<BackendRes<ClusterImagesData>>(
    faceClustersEndpoints.getClusterImages(request.clusterId),
  );
  return response.data;
};

export const fetchSearchedFaces = async (
  request: FetchSearchedFacesRequest,
): Promise<FaceSearchResponse> => {
  const response = await apiClient.post<FaceSearchResponse>(
    faceClustersEndpoints.searchForFaces,
    request,
    { timeout: LONG_REQUEST_TIMEOUT_MS },
  );
  return response.data;
};

export const fetchSearchedFacesBase64 = async (
  request: FetchSearchedFacesBase64Request,
): Promise<FaceSearchResponse> => {
  const response = await apiClient.post<FaceSearchResponse>(
    faceClustersEndpoints.searchForFacesBase64,
    request,
    { timeout: LONG_REQUEST_TIMEOUT_MS },
  );
  return response.data;
};

export interface GlobalReclusterStartData {
  task_id: string;
}

export interface GlobalReclusterStatusData {
  status: 'running' | 'complete' | 'error';
  clusters_created: number | null;
  faces_skipped: number | null;
}

// Reclustering scans every embedding and can exceed any HTTP timeout, so the
// backend runs it as a background job; this kicks it off and returns a task_id.
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
): Promise<BackendRes<MultiPersonSearchData>> => {
  const response = await apiClient.post<BackendRes<MultiPersonSearchData>>(
    faceClustersEndpoints.multiPersonSearch,
    request,
    { timeout: LONG_REQUEST_TIMEOUT_MS },
  );
  return response.data;
};
