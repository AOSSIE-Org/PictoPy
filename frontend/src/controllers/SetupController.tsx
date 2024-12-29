import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFolderPath } from '../hooks/useFolderPath';
import { FolderService } from '@/hooks/folderService';

export const useInitialPageController = () => {
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { setFolderPath } = useFolderPath();

  useEffect(() => {
    const initializePage = async () => {
      const savedFolderPath = await FolderService.getSavedFolderPath();
      if (savedFolderPath) {
        setFolderPath(savedFolderPath);

        navigate('/home');
      }
      setLoading(false);
    };

    initializePage();
  }, []);

  const handleFolderPathChange = async (path: string) => {
    setFolderPath(path);
    await FolderService.saveFolderPath(path);
    path && navigate('/home');
  };

  return { loading, handleFolderPathChange };
};
