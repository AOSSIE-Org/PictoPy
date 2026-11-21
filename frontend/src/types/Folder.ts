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

/**
 * Whether a walk is queued or running.
 *
 * 'interrupted' is a stopped state - a previous session died mid-walk - so it
 * must not read as work in flight, or the card spins on a walk nobody is
 * going to run. An unknown value is treated as pending, matching the old
 * "anything but completed" behaviour.
 */
export const isIndexingPending = (status?: IndexingStatus): boolean =>
  status !== 'completed' && status !== 'interrupted';

/** Number of folders nested anywhere below `folderId`. */
export const countSubfolders = (
  folders: FolderDetails[],
  folderId: string,
): number => {
  const children = new Map<string, string[]>();
  for (const f of folders) {
    if (!f.parent_folder_id) continue;
    const siblings = children.get(f.parent_folder_id);
    if (siblings) siblings.push(f.folder_id);
    else children.set(f.parent_folder_id, [f.folder_id]);
  }
  let count = 0;
  const stack = [...(children.get(folderId) ?? [])];
  while (stack.length) {
    count++;
    stack.push(...(children.get(stack.pop() as string) ?? []));
  }
  return count;
};

export interface GetAllFoldersData {
  folders: FolderDetails[];
  total_count: number;
}
