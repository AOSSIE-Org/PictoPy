export const FolderService = {
  getSavedFolderPath: async (): Promise<string | null> => {
    return localStorage.getItem('folderPath');
  },

  saveFolderPath: async (path: string): Promise<void> => {
    localStorage.setItem('folderPath', path);
  },
};
