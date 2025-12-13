import {
  mergeFoldersWithStatus,
  groupFoldersByStatus,
  calculateFolderStats,
  FolderWithStatus,
} from '../folderUtils';
import { FolderDetails } from '@/types/Folder';
import { FolderTaggingInfo } from '@/types/FolderStatus';

describe('folderUtils', () => {
  const mockFolders: FolderDetails[] = [
    {
      folder_id: '1',
      folder_path: '/photos/vacation',
      last_modified_time: 1000,
      AI_Tagging: true,
    },
    {
      folder_id: '2',
      folder_path: '/photos/family',
      last_modified_time: 2000,
      AI_Tagging: true,
    },
    {
      folder_id: '3',
      folder_path: '/photos/work',
      last_modified_time: 3000,
      AI_Tagging: false,
    },
  ];

  const mockTaggingStatus: Record<string, FolderTaggingInfo> = {
    '1': { folder_id: '1', folder_path: '/photos/vacation', tagging_percentage: 100 },
    '2': { folder_id: '2', folder_path: '/photos/family', tagging_percentage: 50 },
  };

  describe('mergeFoldersWithStatus', () => {
    it('should merge folders with their tagging status', () => {
      const result = mergeFoldersWithStatus(mockFolders, mockTaggingStatus);

      expect(result).toHaveLength(3);
      expect(result[0].tagging_percentage).toBe(100);
      expect(result[1].tagging_percentage).toBe(50);
      expect(result[2].tagging_percentage).toBe(0); // No status, defaults to 0
    });

    it('should handle empty folders', () => {
      const result = mergeFoldersWithStatus([], mockTaggingStatus);
      expect(result).toHaveLength(0);
    });

    it('should handle empty tagging status', () => {
      const result = mergeFoldersWithStatus(mockFolders, {});
      expect(result.every((f) => f.tagging_percentage === 0)).toBe(true);
    });
  });

  describe('groupFoldersByStatus', () => {
    it('should group folders correctly', () => {
      const foldersWithStatus: FolderWithStatus[] = [
        { ...mockFolders[0], tagging_percentage: 100 }, // completed
        { ...mockFolders[1], tagging_percentage: 50 },  // in progress
        { ...mockFolders[2], tagging_percentage: 0 },   // pending (AI_Tagging: false)
      ];

      const result = groupFoldersByStatus(foldersWithStatus);

      expect(result.completed).toHaveLength(1);
      expect(result.completed[0].folder_id).toBe('1');

      expect(result.inProgress).toHaveLength(1);
      expect(result.inProgress[0].folder_id).toBe('2');

      expect(result.pending).toHaveLength(1);
      expect(result.pending[0].folder_id).toBe('3');
    });

    it('should handle all folders being pending', () => {
      const foldersWithStatus: FolderWithStatus[] = mockFolders.map((f) => ({
        ...f,
        AI_Tagging: false,
        tagging_percentage: 0,
      }));

      const result = groupFoldersByStatus(foldersWithStatus);

      expect(result.completed).toHaveLength(0);
      expect(result.inProgress).toHaveLength(0);
      expect(result.pending).toHaveLength(3);
    });

    it('should handle empty array', () => {
      const result = groupFoldersByStatus([]);

      expect(result.completed).toHaveLength(0);
      expect(result.inProgress).toHaveLength(0);
      expect(result.pending).toHaveLength(0);
    });
  });

  describe('calculateFolderStats', () => {
    it('should calculate stats correctly', () => {
      const groupedFolders = {
        completed: [{ ...mockFolders[0], tagging_percentage: 100 }],
        inProgress: [{ ...mockFolders[1], tagging_percentage: 50 }],
        pending: [{ ...mockFolders[2], tagging_percentage: 0 }],
      };

      const result = calculateFolderStats(groupedFolders);

      expect(result.total).toBe(3);
      expect(result.completed).toBe(1);
      expect(result.inProgress).toBe(1);
      expect(result.pending).toBe(1);
      expect(result.overallPercentage).toBe(75); // (100 + 50) / 2
    });

    it('should handle no folders with tagging enabled', () => {
      const groupedFolders = {
        completed: [],
        inProgress: [],
        pending: [{ ...mockFolders[2], tagging_percentage: 0 }],
      };

      const result = calculateFolderStats(groupedFolders);

      expect(result.total).toBe(1);
      expect(result.overallPercentage).toBe(0);
    });

    it('should handle empty groups', () => {
      const groupedFolders = {
        completed: [],
        inProgress: [],
        pending: [],
      };

      const result = calculateFolderStats(groupedFolders);

      expect(result.total).toBe(0);
      expect(result.overallPercentage).toBe(0);
    });
  });
});
