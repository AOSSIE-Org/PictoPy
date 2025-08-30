export interface FolderDetails {
  folder_id: string;
  folder_path: string;
  parent_folder_id?: string;
  last_modified_time: number;
  AI_Tagging: boolean;
  taggingCompleted?: boolean;
}

export interface GetAllFoldersData {
  folders: FolderDetails[];
  total_count: number;
}
