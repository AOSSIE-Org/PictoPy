import React, { useEffect } from 'react';
import { useUpdater } from '@/hooks/useUpdater';
import UpdateDialog from '@/components/Updater/UpdateDialog';
import { useDispatch } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { markCompleted } from '@/features/onboardingSlice';

interface UpdateStepProps {
  stepIndex: number;
}

export const UpdateStep: React.FC<UpdateStepProps> = ({ stepIndex }) => {
  const {
    updateAvailable,
    isDownloading,
    downloadProgress,
    error,
    checkForUpdates,
    downloadAndInstall,
    dismissUpdate,
  } = useUpdater();

  const dispatch = useDispatch();

  useEffect(() => {
    let isMount = true;
    // Check for updates on mount
    const check = async () => {
      if (!isMount) {
        return;
      }
      dispatch(showLoader('Checking for updates...'));
      const hasUpdate = await checkForUpdates();
      dispatch(hideLoader());

      // If no update, mark onboarding step complete
      if (isMount && !hasUpdate) {
        dispatch(markCompleted(stepIndex));
      }
    };
    check();
    return () => {
      isMount = false;
    }
  }, [dispatch,stepIndex, checkForUpdates]);

  // Show update dialog only if update is available
  if (updateAvailable) {
    return (
      <UpdateDialog
        update={updateAvailable}
        onDownload={downloadAndInstall}
        onLater={() => {
          dismissUpdate();
          dispatch(markCompleted(stepIndex));
        }}
        isDownloading={isDownloading}
        downloadProgress={downloadProgress}
        error={error}
        showCloseButton={false}
      />
    );
  } else return null;
};
