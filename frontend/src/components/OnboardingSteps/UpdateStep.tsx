import React, { useEffect } from 'react';
import { useUpdater } from '@/hooks/useUpdater';
import UpdateDialog from '@/components/Updater/UpdateDialog';
import { useDispatch } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { markCompleted } from '@/features/onboardingSlice';

interface UpdateStepProps {
  stepIndex: number;
}
export const UpdateStep: React.FC<UpdateStepProps> = ({
  stepIndex,
}: UpdateStepProps) => {
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
    let check = async () => {
      dispatch(showLoader('Checking for updates...'));
      const hasUpdate = await checkForUpdates();
      dispatch(hideLoader());
      if (!hasUpdate) {
        dispatch(markCompleted(stepIndex));
      }
    };
    check();
  }, []);

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
  }
};
