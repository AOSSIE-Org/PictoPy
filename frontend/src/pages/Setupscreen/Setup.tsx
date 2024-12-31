import React from 'react';
import { useInitialPageController } from '@/controllers/SetupController';
import { SetupScreen } from '@/features/Setup/Setup';
import { LoadingScreen } from '@/components/LoadingScreen/LoadingScreen';

export const InitialPage: React.FC = () => {
  const { loading, handleFolderPathChange } = useInitialPageController();
  if (loading) {
    return <LoadingScreen />;
  }

  return <SetupScreen onFolderPathChange={handleFolderPathChange} />;
};
