import React from 'react';
import { useInitialPageController } from '@/controllers/InitialPageController';
import { SetupScreen } from '@/features/Setup/SetupScreen';

type Props = {
  onNext: () => void;
};

export const FolderSetupStep: React.FC<Props> = ({ onNext }) => {
  const { handleFolderPathsChange, folderPaths } = useInitialPageController();
  if (folderPaths.length > 0) {
    onNext();
  }
  const handleChange = async (paths: string[]) => {
    await handleFolderPathsChange(paths);
    if (paths.length > 0) {
      onNext();
    }
  };

  return <SetupScreen onFolderPathsChange={handleChange} />;
};
