export interface FolderTaggingInfo {
  folder_id: string;
  folder_path: string;
  tagging_percentage: number; // 0 - 100
  embedding_percentage: number; // 0 - 100
  total_images: number;
  tagged_images: number;
  embedded_images: number;
  total_videos: number;
  tagged_videos: number;
  embedded_videos: number;
  ai_tagging: boolean;
}

export interface FolderTaggingStatusResponse {
  status: 'success' | 'error';
  data: FolderTaggingInfo[];
  total_folders: number;
  message?: string;
}
