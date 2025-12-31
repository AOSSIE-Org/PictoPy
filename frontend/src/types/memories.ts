/**
 * TypeScript type definitions for the Memories feature
 */

export interface ImageBasic {
  id: number;
  path: string;
  date_taken?: string;
  latitude?: number;
  longitude?: number;
}

export interface CoverImage {
  id: number;
  path: string;
}

export interface Memory {
  id?: number;
  type: 'time_based' | 'location_based';
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  cover_image: CoverImage;
  image_count: number;
  images: ImageBasic[];
  created_at?: string;
  last_viewed?: string;
  years_ago?: number;
}

export interface MemoriesListResponse {
  memories: Memory[];
  total_count: number;
}

export interface GenerateMemoriesRequest {
  include_time_based?: boolean;
  include_location_based?: boolean;
  reference_date?: string;
  min_images_for_location?: number;
  distance_threshold?: number;
}

export interface GenerateMemoriesResponse {
  success: boolean;
  message: string;
  time_based_count: number;
  location_based_count: number;
  total_memories: number;
}

export interface DeleteMemoryResponse {
  success: boolean;
  message: string;
}
