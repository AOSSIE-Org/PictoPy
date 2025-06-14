import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useFolderPaths } from '@/hooks/useFolderPath';
import { FolderService } from '@/hooks/folderService';
import { useLoading } from '@/hooks/useLoading';
import { ROUTES } from '@/constants/routes';

export const useInitialPageController = () => {
  const { showLoader, hideLoader } = useLoading();
  const navigate = useNavigate();
  const { folderPaths, setFolderPaths } = useFolderPaths();

  useEffect(() => {
    const initializePage = async () => {
      showLoader('Loading');
      const savedFolderPaths = await FolderService.getSavedFolderPaths();
      hideLoader();
      if (savedFolderPaths && savedFolderPaths.length > 0) {
        setFolderPaths(savedFolderPaths);
        navigate(`/${ROUTES.LAYOUT.HOME}`);
      }
    };

    initializePage();
  }, []);

  const handleFolderPathsChange = async (paths: string[]) => {
    setFolderPaths(paths);
    await FolderService.saveFolderPaths(paths);
    paths.length > 0 && navigate(`/${ROUTES.LAYOUT.HOME}`);
  };

  return { handleFolderPathsChange, folderPaths };
};
