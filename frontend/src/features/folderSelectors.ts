import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';
import { FolderDetails } from '@/types/Folder';

// Basic selectors
export const selectFolderState = (state: RootState) => state.folders;

export const selectAllFolders = (state: RootState) => state.folders.folders;

// Memoized selectors using createSelector
export const selectFolderById = createSelector(
  [selectAllFolders, (_: RootState, folderId: string) => folderId],
  (folders, folderId) =>
    folders.find((folder) => folder.folder_id === folderId),
);

export const selectFoldersByParentId = createSelector(
  [selectAllFolders, (_: RootState, parentId: string | null) => parentId],
  (folders, parentId) =>
    folders.filter((folder) => folder.parent_folder_id === parentId),
);

// Get root folders (folders with no parent)
export const selectRootFolders = createSelector([selectAllFolders], (folders) =>
  folders.filter((folder) => !folder.parent_folder_id),
);

// Get folders with AI tagging enabled
export const selectAITaggingEnabledFolders = createSelector(
  [selectAllFolders],
  (folders) => folders.filter((folder) => folder.AI_Tagging),
);

// Get folders with tagging completed
export const selectTaggingCompletedFolders = createSelector(
  [selectAllFolders],
  (folders) => folders.filter((folder) => folder.taggingCompleted),
);

// Get folders by path pattern (case-insensitive search)
export const selectFoldersByPathPattern = createSelector(
  [selectAllFolders, (_: RootState, pattern: string) => pattern.toLowerCase()],
  (folders, pattern) =>
    folders.filter((folder) =>
      folder.folder_path.toLowerCase().includes(pattern),
    ),
);

// Folder hierarchy selectors
export const selectFolderHierarchy = createSelector(
  [selectAllFolders],
  (folders) => {
    const buildHierarchy = (
      parentId: string | null = null,
    ): FolderDetails[] => {
      return folders
        .filter((folder) => folder.parent_folder_id === parentId)
        .map((folder) => ({
          ...folder,
          children: buildHierarchy(folder.folder_id),
        }));
    };

    return buildHierarchy();
  },
);

// Statistics selectors
export const selectFolderStats = createSelector(
  [selectAllFolders],
  (folders) => ({
    total: folders.length,
    withAITagging: folders.filter((f) => f.AI_Tagging).length,
    taggingCompleted: folders.filter((f) => f.taggingCompleted).length,
    rootFolders: folders.filter((f) => !f.parent_folder_id).length,
  }),
);

// Recent folders (by last_modified_time)
export const selectRecentFolders = createSelector(
  [selectAllFolders, (_: RootState, limit: number = 10) => limit],
  (folders, limit) =>
    [...folders]
      .sort((a, b) => b.last_modified_time - a.last_modified_time)
      .slice(0, limit),
);

// Folders grouped by parent
export const selectFoldersGroupedByParent = createSelector(
  [selectAllFolders],
  (folders) => {
    const grouped: Record<string, FolderDetails[]> = {};
    folders.forEach((folder) => {
      const parentKey = folder.parent_folder_id || 'root';
      if (!grouped[parentKey]) {
        grouped[parentKey] = [];
      }
      grouped[parentKey].push(folder);
    });
    return grouped;
  },
);
