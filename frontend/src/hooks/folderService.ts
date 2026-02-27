import logger from '@/utils/logger';

const FOLDER_PATHS_KEY = 'folderPaths';

export const FolderService = {
  getSavedFolderPaths: (): string[] => {
    try {
      const raw = localStorage.getItem(FOLDER_PATHS_KEY);
      const parsed = raw ? JSON.parse(raw) : [];

      if (Array.isArray(parsed) && parsed.every((p) => typeof p === 'string')) {
        return parsed;
      }

      // Malformed structure: reset to empty array
      localStorage.setItem(FOLDER_PATHS_KEY, JSON.stringify([]));
      return [];
    } catch (error) {
      logger.error(
        'Error reading or parsing folder paths from localStorage:',
        error,
      );
      localStorage.setItem(FOLDER_PATHS_KEY, JSON.stringify([]));
      return [];
    }
  },

  saveFolderPaths: (paths: string[]) => {
    try {
      localStorage.setItem(FOLDER_PATHS_KEY, JSON.stringify(paths));
    } catch (error) {
      logger.error('Error saving folder paths to localStorage:', error);
    }
  },
};
