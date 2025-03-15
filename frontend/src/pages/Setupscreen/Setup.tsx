import React from 'react';
import { useInitialPageController } from '@/controllers/InitialPageController';
import { SetupScreen } from '@/features/Setup/SetupScreen';
import { LoadingScreen } from '@/components/LoadingScreen/LoadingScreen';

export const InitialPage: React.FC = () => {
  const { loading, handleFolderPathsChange } = useInitialPageController();
  if (loading)
    <div className="flex h-full w-full items-center justify-center">
      <LoadingScreen />
    </div>;

  return <SetupScreen onFolderPathsChange={handleFolderPathsChange} />;
};
