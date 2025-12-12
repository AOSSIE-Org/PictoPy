import { smartAlbumsEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';


// ==================== TYPE DEFINITIONS ====================

export interface SmartAlbumCriteria {
  type: 'object' | 'face';
  class_names?: string[];
  class_ids?: number[];
  face_id?: string;
  date_range?: {
    start?: number;
    end?: number;
  };
}

export interface SmartAlbum {
  album_id: string;
  album_name: string;
  album_type: 'object' | 'face';
  criteria: SmartAlbumCriteria;
  thumb_image_id?: string;
  auto_update: boolean;
  created_at: number;
  updated_at: number;
  image_count: number;
}

export interface AlbumImage {
  id: string;
  path: string;
  folder_id: string;
  thumbnailPath: string;
  metadata: Record<string, any>;
  isTagged: boolean;
  isFavourite: boolean;
  album_added_at: number;
}

export interface CreateObjectAlbumRequest {
  album_name: string;
  object_classes: string[];
  auto_update: boolean;
}

export interface CreateFaceAlbumRequest {
  album_name: string;
  face_id: string;
  auto_update: boolean;
}

export interface UpdateAlbumRequest {
  album_name?: string;
  auto_update?: boolean;
}

export interface AlbumStatistics {
  total_albums: number;
  object_albums: number;
  face_albums: number;
  auto_update_enabled: number;
  total_images_in_albums: number;
}

// ==================== RESPONSE TYPES ====================

interface SmartAlbumsResponse {
  success: boolean;
  albums: SmartAlbum[];
  count: number;
}

interface AlbumDetailsResponse {
  success: boolean;
  album: SmartAlbum;
}

interface AlbumImagesResponse {
  success: boolean;
  album_id: string;
  images: AlbumImage[];
  count: number;
  limit?: number;
  offset: number;
}

interface CreateAlbumResponse {
  success: boolean;
  album: SmartAlbum;
  message: string;
}

interface RefreshAlbumResponse {
  success: boolean;
  album_id: string;
  updated_image_count: number;
  album: SmartAlbum;
  message: string;
}

interface RefreshAllResponse {
  success: boolean;
  refreshed_albums: Record<string, number>;
  albums: SmartAlbum[];
  album_count: number;
  total_images: number;
  message: string;
}

interface AvailableClassesResponse {
  success: boolean;
  available_classes: string[];
  count: number;
  message: string;
}

interface StatisticsResponse {
  success: boolean;
  statistics: AlbumStatistics;
  message: string;
}

interface DeleteAlbumResponse {
  success: boolean;
  album_id: string;
  message: string;
}

interface PredefinedAlbumsResponse {
  success: boolean;
  albums: SmartAlbum[];
  created_count: number;
  message: string;
}

// ==================== API FUNCTIONS ====================

/**
 * Get all smart albums
 */
export const getAllSmartAlbums = async (): Promise<SmartAlbum[]> => {
  const res = await apiClient.get<SmartAlbumsResponse>(
    smartAlbumsEndpoints.getAllAlbums
  );
  return res.data.albums; 
};

/**
 * Get specific album details by ID
 */
export const getSmartAlbumDetails = async (
  albumId: string
): Promise<SmartAlbum> => {
  const res = await apiClient.get<AlbumDetailsResponse>(
    smartAlbumsEndpoints.getAlbumDetails(albumId)
  );
  return res.data.album; 
};

/**
 * Get images in an album with pagination
 */
export const getSmartAlbumImages = async (
  albumId: string,
  limit?: number,
  offset?: number
): Promise<AlbumImage[]> => {
  const res = await apiClient.get<AlbumImagesResponse>(
    smartAlbumsEndpoints.getAlbumImages(albumId, limit, offset)
  );
  return res.data.images; 
};

/**
 * Create object-based smart album
 */
export const createObjectAlbum = async (
  request: CreateObjectAlbumRequest
): Promise<SmartAlbum> => {
  const res = await apiClient.post<CreateAlbumResponse>(
    smartAlbumsEndpoints.createObjectAlbum,
    request
  );
  return res.data.album;
};

/**
 * Create face-based smart album
 */
export const createFaceAlbum = async (
  request: CreateFaceAlbumRequest
): Promise<SmartAlbum> => {
  const res = await apiClient.post<CreateAlbumResponse>(
    smartAlbumsEndpoints.createFaceAlbum,
    request
  );
  return res.data.album;
};

/**
 * Create predefined albums (People, Animals, Vehicles, etc.)
 */
export const createPredefinedAlbums = async (): Promise<{
  albums: SmartAlbum[];
  created_count: number;
  message: string;
}> => {
  const res = await apiClient.post<PredefinedAlbumsResponse>(
    smartAlbumsEndpoints.createPredefinedAlbums
  );
  return {
    albums: res.data.albums,
    created_count: res.data.created_count,
    message: res.data.message,
  };
};

/**
 * Refresh a single album
 */
export const refreshAlbum = async (
  albumId: string
): Promise<{
  updated_image_count: number;
  album: SmartAlbum;
  message: string;
}> => {
  const res = await apiClient.post<RefreshAlbumResponse>(
    smartAlbumsEndpoints.refreshAlbum(albumId)
  );
  return {
    updated_image_count: res.data.updated_image_count,
    album: res.data.album,
    message: res.data.message,
  };
};

/**
 * Refresh all albums
 */
export const refreshAllAlbums = async (): Promise<{
  refreshed_albums: Record<string, number>;
  albums: SmartAlbum[];
  album_count: number;
  total_images: number;
  message: string;
}> => {
  const res = await apiClient.post<RefreshAllResponse>(
    smartAlbumsEndpoints.refreshAllAlbums
  );
  return {
    refreshed_albums: res.data.refreshed_albums,
    albums: res.data.albums,
    album_count: res.data.album_count,
    total_images: res.data.total_images,
    message: res.data.message,
  };
};

/**
 * Update album name or auto-update setting
 */
export const updateAlbum = async (
  albumId: string,
  request: UpdateAlbumRequest
): Promise<SmartAlbum> => {
  const res = await apiClient.patch<CreateAlbumResponse>(
    smartAlbumsEndpoints.updateAlbum(albumId),
    request
  );
  return res.data.album;
};

/**
 * Delete a smart album
 */
export const deleteAlbum = async (
  albumId: string
): Promise<{ album_id: string; message: string }> => {
  const res = await apiClient.delete<DeleteAlbumResponse>(
    smartAlbumsEndpoints.deleteAlbum(albumId)
  );
  return {
    album_id: res.data.album_id,
    message: res.data.message,
  };
};

/**
 * Get available YOLO object classes
 */
export const getAvailableClasses = async (): Promise<string[]> => {
  const res = await apiClient.get<AvailableClassesResponse>(
    smartAlbumsEndpoints.getAvailableClasses
  );
  return res.data.available_classes;
};

/**
 * Get album statistics
 */
export const getAlbumStatistics = async (): Promise<AlbumStatistics> => {
  const res = await apiClient.get<StatisticsResponse>(
    smartAlbumsEndpoints.getStatistics
  );
  return res.data.statistics;
};