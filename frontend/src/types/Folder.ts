export interface FolderDetails {
  folder_id: string;
  folder_path: string;
  parent_folder_id?: string;
  last_modified_time: number;
  AI_Tagging: boolean;
  taggingCompleted?: boolean;
  image_count?: number;
  video_count?: number;
  indexing_status?: IndexingStatus;
}

export type IndexingStatus =
  | 'not_started'
  | 'in_progress'
  | 'completed'
  | 'interrupted';

// 'interrupted' is stopped, not in flight, or the card spins on a walk nobody
// will run. Unknown reads as pending, matching the old "anything but completed".
export const isIndexingPending = (status?: IndexingStatus): boolean =>
  status !== 'completed' && status !== 'interrupted';

export interface GetAllFoldersData {
  folders: FolderDetails[];
  total_count: number;
}
