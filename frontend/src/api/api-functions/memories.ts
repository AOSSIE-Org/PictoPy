import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

// Request Types
export interface GenerateMemoriesRequest {
  location_radius_km?: number;
  date_tolerance_days?: number;
  min_images?: number;
}

// Data Types
/**
 * Individual image within a memory
 */
export interface MemoryImage {
  id: string;
  path: string;
  thumbnailPath: string;
  latitude: number | null;
  longitude: number | null;
  captured_at: string | null;
  isFavourite?: boolean;
}

/**
 * Memory object representing a collection of photos
 */
export interface Memory {
  memory_id: string;
  title: string;
  description: string;
  location_name: string;
  date_start: string | null;
  date_end: string | null;
  image_count: number;
  images: MemoryImage[];
  thumbnail_image_id: string;
  center_lat: number | null;
  center_lon: number | null;
}

/**
 * Location cluster with sample images
 */
export interface LocationCluster {
  location_name: string;
  center_lat: number;
  center_lon: number;
  image_count: number;
  sample_images: MemoryImage[];
}

// API Functions
/**
 * Generate all memories from images with location data
 */
export const generateMemories = async (
  request?: GenerateMemoriesRequest,
): Promise<APIResponse> => {
  const params = new URLSearchParams();
  if (request?.location_radius_km)
    params.append('location_radius_km', request.location_radius_km.toString());
  if (request?.date_tolerance_days)
    params.append(
      'date_tolerance_days',
      request.date_tolerance_days.toString(),
    );
  if (request?.min_images)
    params.append('min_images', request.min_images.toString());

  const url = `${memoriesEndpoints.generate}${params.toString() ? '?' + params.toString() : ''}`;
  const response = await apiClient.post<APIResponse>(url);
  return response.data;
};

/**
 * Get memories from the past N days as a timeline
 */
export const getTimeline = async (
  days: number = 365,
  options?: {
    location_radius_km?: number;
    date_tolerance_days?: number;
  },
): Promise<APIResponse> => {
  const params = new URLSearchParams();
  params.append('days', days.toString());
  if (options?.location_radius_km)
    params.append('location_radius_km', options.location_radius_km.toString());
  if (options?.date_tolerance_days)
    params.append(
      'date_tolerance_days',
      options.date_tolerance_days.toString(),
    );

  const response = await apiClient.get<APIResponse>(
    `${memoriesEndpoints.timeline}?${params.toString()}`,
  );
  return response.data;
};

/**
 * Get photos taken on this date in previous years
 */
export const getOnThisDay = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    memoriesEndpoints.onThisDay,
  );
  return response.data;
};

/**
 * Get all unique locations where photos were taken
 */
export const getLocations = async (options?: {
  location_radius_km?: number;
  max_sample_images?: number;
}): Promise<APIResponse> => {
  const params = new URLSearchParams();
  if (options?.location_radius_km)
    params.append('location_radius_km', options.location_radius_km.toString());
  if (options?.max_sample_images)
    params.append('max_sample_images', options.max_sample_images.toString());

  const url = `${memoriesEndpoints.locations}${params.toString() ? '?' + params.toString() : ''}`;
  const response = await apiClient.get<APIResponse>(url);
  return response.data;
};
