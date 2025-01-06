export const FolderService = {
  getSavedFolderPaths: async (): Promise<string[] | null> => {
    const paths = localStorage.getItem('folderPaths');
    return paths ? JSON.parse(paths) : null;
  },

  saveFolderPaths: async (paths: string[]): Promise<void> => {
    localStorage.setItem('folderPaths', JSON.stringify(paths));
  },
};
