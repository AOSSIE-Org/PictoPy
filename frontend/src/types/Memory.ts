import { Image } from './Media';

export interface OnThisDayMemory {
  year: number;
  years_ago: number;
  date: string;
  images: Image[];
}

export interface RecentMemory {
  date: string;
  iso_date: string;
  images: Image[];
}

export interface PersonMemory {
  cluster_id: string;
  person_name: string;
  image_count: number;
  images: Image[];
}

export interface TagMemory {
  tag_name: string;
  image_count: number;
  images: Image[];
}

export interface AllMemoriesData {
  on_this_day: OnThisDayMemory[];
  recent: RecentMemory[];
  people: PersonMemory[];
  tags: TagMemory[];
}

export interface MemoriesResponse {
  success: boolean;
  message: string;
  data: AllMemoriesData;
}

export type MemoryType = 'on_this_day' | 'recent' | 'people' | 'tags';
