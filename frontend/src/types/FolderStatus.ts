export interface FolderTaggingInfo {
  folder_id: string;
  folder_path: string;
  total_images: number;        
  tagged_images: number; 
  tagging_percentage: number; // 0 - 100
}

export interface FolderTaggingStatusResponse {
  status: 'success' | 'error';
  data: FolderTaggingInfo[];
  total_folders: number;
  message?: string;
}
