import { faceClustersEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { BackendRes } from '@/hooks/useQueryExtension';
import type { FaceMatchMode, Image, ImageMetadata, Video } from '@/types/Media';

//Request Types
export interface RenameClusterRequest {
  clusterId: string;
  newName: string;
}
export interface FetchClusterImagesRequest {
  clusterId: string;
}

/** Which faces of the query photo to search with; omitted means the first. */
export interface FaceSelectionParams {
  face_indices?: number[];
  match_mode?: FaceMatchMode;
}

export interface FetchSearchedFacesRequest extends FaceSelectionParams {
  path: string;
}

export interface FetchSearchedFacesBase64Request extends FaceSelectionParams {
  base64_data: string;
}

export type FetchDetectedFacesRequest = Pick<FetchSearchedFacesRequest, 'path'>;

export type FetchDetectedFacesBase64Request = Pick<
  FetchSearchedFacesBase64Request,
  'base64_data'
>;

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

/** A face found in the query photo; `bbox` is in source-image pixels. */
export interface DetectedFace {
  index: number;
  bbox: { x: number; y: number; width: number; height: number };
  confidence: number;
}

export interface DetectedFacesData {
  image_width: number;
  image_height: number;
  faces: DetectedFace[];
  faces_skipped: number;
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
  );
  return response.data;
};

export const fetchSearchedFacesBase64 = async (
  request: FetchSearchedFacesBase64Request,
): Promise<FaceSearchResponse> => {
  const response = await apiClient.post<FaceSearchResponse>(
    faceClustersEndpoints.searchForFacesBase64,
    request,
  );
  return response.data;
};

export const fetchDetectedFaces = async (
  request: FetchDetectedFacesRequest,
): Promise<BackendRes<DetectedFacesData | null>> => {
  const response = await apiClient.post<BackendRes<DetectedFacesData | null>>(
    faceClustersEndpoints.detectFaces,
    request,
  );
  return response.data;
};

export const fetchDetectedFacesBase64 = async (
  request: FetchDetectedFacesBase64Request,
): Promise<BackendRes<DetectedFacesData | null>> => {
  const response = await apiClient.post<BackendRes<DetectedFacesData | null>>(
    faceClustersEndpoints.detectFacesBase64,
    request,
  );
  return response.data;
};

export interface GlobalReclusterData {
  clusters_created: number | null;
  faces_skipped: number | null;
}

export const triggerGlobalReclustering = async (): Promise<
  BackendRes<GlobalReclusterData>
> => {
  const response = await apiClient.post<BackendRes<GlobalReclusterData>>(
    faceClustersEndpoints.globalRecluster,
  );
  return response.data;
};

export interface MultiPersonSearchRequest {
  cluster_ids: string[];
  match_mode: FaceMatchMode;
}

export const fetchMultiPersonSearch = async (
  request: MultiPersonSearchRequest,
): Promise<BackendRes<MultiPersonSearchData>> => {
  const response = await apiClient.post<BackendRes<MultiPersonSearchData>>(
    faceClustersEndpoints.multiPersonSearch,
    request,
  );
  return response.data;
};
