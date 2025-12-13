import { FolderDetails } from '@/types/Folder';
import { FolderTaggingInfo } from '@/types/FolderStatus';

export interface FolderWithStatus extends FolderDetails {
  tagging_percentage: number;
}

export interface GroupedFolders {
  completed: FolderWithStatus[];
  inProgress: FolderWithStatus[];
  pending: FolderWithStatus[];
}

export interface FolderStats {
  total: number;
  completed: number;
  inProgress: number;
  pending: number;
  overallPercentage: number;
}

/**
 * Merges folder details with their tagging status
 */
export const mergeFoldersWithStatus = (
  folders: FolderDetails[],
  taggingStatus: Record<string, FolderTaggingInfo>,
): FolderWithStatus[] => {
  return folders.map((folder) => ({
    ...folder,
    tagging_percentage: taggingStatus[folder.folder_id]?.tagging_percentage ?? 0,
  }));
};

/**
 * Groups folders by their tagging status
 * - Completed: AI_Tagging enabled AND 100% tagged
 * - In Progress: AI_Tagging enabled AND < 100% tagged
 * - Pending: AI_Tagging disabled
 */
export const groupFoldersByStatus = (
  folders: FolderWithStatus[],
): GroupedFolders => {
  const completed: FolderWithStatus[] = [];
  const inProgress: FolderWithStatus[] = [];
  const pending: FolderWithStatus[] = [];

  for (const folder of folders) {
    if (!folder.AI_Tagging) {
      pending.push(folder);
    } else if (folder.tagging_percentage >= 100) {
      completed.push(folder);
    } else {
      inProgress.push(folder);
    }
  }

  return { completed, inProgress, pending };
};

/**
 * Calculates folder statistics
 */
export const calculateFolderStats = (
  groupedFolders: GroupedFolders,
): FolderStats => {
  const { completed, inProgress, pending } = groupedFolders;
  const total = completed.length + inProgress.length + pending.length;

  // Calculate overall percentage based on folders with AI tagging enabled
  const foldersWithTagging = [...completed, ...inProgress];
  const overallPercentage =
    foldersWithTagging.length > 0
      ? foldersWithTagging.reduce((sum, f) => sum + f.tagging_percentage, 0) /
        foldersWithTagging.length
      : 0;

  return {
    total,
    completed: completed.length,
    inProgress: inProgress.length,
    pending: pending.length,
    overallPercentage: Math.round(overallPercentage),
  };
};

/**
 * Storage key for persisting user preferences
 */
export const FOLDER_PREFS_KEY = 'pictopy_folder_preferences';

export interface FolderPreferences {
  collapsedSections: {
    completed: boolean;
    inProgress: boolean;
    pending: boolean;
  };
}

export const defaultFolderPreferences: FolderPreferences = {
  collapsedSections: {
    completed: false,
    inProgress: false,
    pending: false,
  },
};

export const loadFolderPreferences = (): FolderPreferences => {
  try {
    const stored = localStorage.getItem(FOLDER_PREFS_KEY);
    if (stored) {
      return { ...defaultFolderPreferences, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.warn('Failed to load folder preferences:', e);
  }
  return defaultFolderPreferences;
};

export const saveFolderPreferences = (prefs: FolderPreferences): void => {
  try {
    localStorage.setItem(FOLDER_PREFS_KEY, JSON.stringify(prefs));
  } catch (e) {
    console.warn('Failed to save folder preferences:', e);
  }
};
