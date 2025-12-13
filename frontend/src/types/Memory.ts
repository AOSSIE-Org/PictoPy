// src/types/Memory.ts

import { ImageMetadata } from './Media';

export interface MemorySummary {
  id: string;
  title: string;
  memory_type: string;
  start_date: string;
  end_date: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  total_photos: number;
  representative_thumbnails: string[];
  created_at: string;
}

export interface ImageInMemory {
  id: string;
  path: string;
  thumbnailPath: string;
  metadata: ImageMetadata;
  is_representative: boolean;
}

export interface MemoryDetail {
  id: string;
  title: string;
  memory_type: string;
  start_date: string;
  end_date: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  cover_image_id?: string;
  total_photos: number;
  created_at: string;
  images: ImageInMemory[];
}

export interface GenerateMemoriesRequest {
  force_regenerate?: boolean;
}

export interface GenerateMemoriesResponse {
  success: boolean;
  message: string;
  data: {
    memories_created: number;
    stats: {
      on_this_day: number;
      trip: number;
      location: number;
      month_highlight: number;
    };
  };
}