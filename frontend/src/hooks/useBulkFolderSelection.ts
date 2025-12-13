import { useState, useCallback, useMemo } from 'react';
import { FolderWithStatus } from '@/utils/folderUtils';

interface UseBulkFolderSelectionReturn {
  selectedIds: Set<string>;
  isSelected: (folderId: string) => boolean;
  toggleSelection: (folderId: string) => void;
  selectAll: (folders: FolderWithStatus[]) => void;
  deselectAll: () => void;
  selectByStatus: (
    folders: FolderWithStatus[],
    status: 'completed' | 'inProgress' | 'pending',
  ) => void;
  selectedCount: number;
  isAllSelected: (folders: FolderWithStatus[]) => boolean;
  getSelectedFolders: (folders: FolderWithStatus[]) => FolderWithStatus[];
}

/**
 * Hook for managing bulk folder selection state
 */
export const useBulkFolderSelection = (): UseBulkFolderSelectionReturn => {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const isSelected = useCallback(
    (folderId: string) => selectedIds.has(folderId),
    [selectedIds],
  );

  const toggleSelection = useCallback((folderId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback((folders: FolderWithStatus[]) => {
    setSelectedIds(new Set(folders.map((f) => f.folder_id)));
  }, []);

  const deselectAll = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const selectByStatus = useCallback(
    (
      folders: FolderWithStatus[],
      status: 'completed' | 'inProgress' | 'pending',
    ) => {
      const filtered = folders.filter((folder) => {
        if (status === 'pending') return !folder.AI_Tagging;
        if (status === 'completed')
          return folder.AI_Tagging && folder.tagging_percentage >= 100;
        return folder.AI_Tagging && folder.tagging_percentage < 100;
      });
      setSelectedIds(new Set(filtered.map((f) => f.folder_id)));
    },
    [],
  );

  const selectedCount = useMemo(() => selectedIds.size, [selectedIds]);

  const isAllSelected = useCallback(
    (folders: FolderWithStatus[]) => {
      if (folders.length === 0) return false;
      return folders.every((f) => selectedIds.has(f.folder_id));
    },
    [selectedIds],
  );

  const getSelectedFolders = useCallback(
    (folders: FolderWithStatus[]) => {
      return folders.filter((f) => selectedIds.has(f.folder_id));
    },
    [selectedIds],
  );

  return {
    selectedIds,
    isSelected,
    toggleSelection,
    selectAll,
    deselectAll,
    selectByStatus,
    selectedCount,
    isAllSelected,
    getSelectedFolders,
  };
};

export default useBulkFolderSelection;
