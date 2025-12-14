export interface Memory {
  id: string;
  title: string;
  description: string | null;
  memory_type: 'on_this_day' | 'location_trip' | string;
  date_range_start: string;
  date_range_end: string;
  location: string | null;
  latitude: number | null;
  longitude: number | null;
  image_count: number;
  cover_image_id: string | null;
  created_at: string;
  last_shown_at: string | null;
  image_ids: string[];
}

export interface MemoryListResponse {
  memories: Memory[];
  total: number;
}

export interface GenerateMemoriesResponse {
  success: boolean;
  generated_count: number;
  message: string;
}
