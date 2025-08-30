import { useState } from 'react';

export const useFolderPaths = () => {
  const [folderPaths, setFolderPaths] = useState<string[]>([]);
  return { folderPaths, setFolderPaths };
};
