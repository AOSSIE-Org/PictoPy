import React from 'react';
import { useInitialPageController } from '@/controllers/InitialPageController';
import { SetupScreen } from '@/features/Setup/SetupScreen';
import { LoadingScreen } from '@/components/LoadingScreen/LoadingScreen';

export const InitialPage: React.FC = () => {
  const { loading, handleFolderPathsChange } = useInitialPageController();
  if (loading) {
    return <LoadingScreen />;
  }

  return <SetupScreen onFolderPathsChange={handleFolderPathsChange} />;
};
