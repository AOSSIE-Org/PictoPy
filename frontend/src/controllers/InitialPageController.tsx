import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFolderPaths } from '../hooks/useFolderPath';
import { FolderService } from '@/hooks/folderService';

export const useInitialPageController = () => {
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { setFolderPaths } = useFolderPaths();

  useEffect(() => {
    const initializePage = async () => {
      const savedFolderPaths = await FolderService.getSavedFolderPaths();
      if (savedFolderPaths && savedFolderPaths.length > 0) {
        setFolderPaths(savedFolderPaths);
        navigate('/home');
      }
      setLoading(false);
    };

    initializePage();
  }, []);

  const handleFolderPathsChange = async (paths: string[]) => {
    setFolderPaths(paths);
    await FolderService.saveFolderPaths(paths);
    paths.length > 0 && navigate('/home');
  };

  return { loading, handleFolderPathsChange };
};