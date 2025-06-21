import React, { useEffect, useState } from 'react';
import { SetupScreen } from '@/components/SetupScreen';
import { FolderService } from '@/hooks/folderService';
import { useDispatch } from 'react-redux';
import { markCompleted } from '@/features/onboardingSlice';

interface FolderSetupStepProps {
  stepIndex: number;
}
export const FolderSetupStep: React.FC<FolderSetupStepProps> = ({
  stepIndex,
}: FolderSetupStepProps) => {
  const dispatch = useDispatch();
  const [folderPaths, setFolderPaths] = useState<string[]>(
    FolderService.getSavedFolderPaths(),
  );
  const [showSetupScreen, setShowSetupScreen] = useState<boolean>(
    folderPaths.length === 0,
  );

  useEffect(() => {
    if (folderPaths.length > 0) {
      setShowSetupScreen(false);
      dispatch(markCompleted(stepIndex));
    }
  }, [folderPaths]);

  const handleFolderPathsChange = (paths: string[]) => {
    setFolderPaths(paths);
    FolderService.saveFolderPaths(paths);
    dispatch(markCompleted(stepIndex));
  };
  return showSetupScreen ? (
    <SetupScreen onFolderPathsChange={handleFolderPathsChange} />
  ) : (
    <div></div>
  );
};
