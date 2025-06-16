import React, { useEffect } from 'react';
import { useUpdater } from '@/hooks/useUpdater';
import UpdateDialog from '@/components/Updater/UpdateDialog';
import { useLoading } from '@/hooks/useLoading';

type Props = {
  onNext: () => void;
};

export const UpdateStep: React.FC<Props> = ({ onNext }) => {
  const {
    updateAvailable,
    isDownloading,
    downloadProgress,
    error,
    checkForUpdates,
    downloadAndInstall,
    dismissUpdate,
  } = useUpdater();
  const { showLoader, hideLoader } = useLoading();
  useEffect(() => {
    let check = async () => {
      showLoader('Checking for updates...');
      const hasUpdate = await checkForUpdates();
      console.log('Update check completed:', hasUpdate);
      hideLoader();
      if (!hasUpdate) onNext();
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
          onNext();
        }}
        isDownloading={isDownloading}
        downloadProgress={downloadProgress}
        error={error}
        showCloseButton={false}
      />
    );
  }
};
