import { useState } from 'react';

export const useFolderPath = () => {
  const [folderPath, setFolderPath] = useState<string>('');
  return { folderPath, setFolderPath };
};
