import React, { useEffect, useState } from 'react';
import { useInitialPageController } from '@/controllers/SetupController';
import { SetupScreen } from '@/features/Setup/Setup';
import { LoadingScreen } from '@/components/LoadingScreen/LoadingScreen';

export const InitialPage: React.FC = () => {
  const {  handleFolderPathChange } = useInitialPageController();
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
    }, 1000);

  }, []);
  
  if (loading) {
    return <LoadingScreen />;
  }
  
  return <SetupScreen onFolderPathChange={handleFolderPathChange} />;
};
