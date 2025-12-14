import { Memory, Image } from '@/types/Media';

export interface MemoriesApiResponse {
  success: boolean;
  data: Memory[];
}

export interface MemoryImagesApiResponse {
  success: boolean;
  data: Image[];
}
