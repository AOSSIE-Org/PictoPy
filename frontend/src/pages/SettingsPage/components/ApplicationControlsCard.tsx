import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  RefreshCw,
  Server,
  Users,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import UpdateDialog from '@/components/Updater/UpdateDialog';
import SettingsCard from './SettingsCard';

import { restartServer } from '@/utils/serverUtils';
import { useUpdater } from '@/hooks/useUpdater';
import { useDispatch } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { triggerGlobalReclustering } from '@/api/api-functions/face_clusters';

/**
 * Component for application controls in settings
 */
const ApplicationControlsCard: React.FC = () => {
  const dispatch = useDispatch();

  const {
    updateAvailable,
    isDownloading,
    downloadProgress,
    error,
    checkForUpdates,
    downloadAndInstall,
    dismissUpdate,
  } = useUpdater();

  const [updateDialogOpen, setUpdateDialogOpen] = useState<boolean>(false);

  const onGlobalReclusterClick = async () => {
    dispatch(showLoader('Starting global face reclustering...'));

    try {
      const response = await triggerGlobalReclustering();

      dispatch(hideLoader());

      if (response.success) {
        setTimeout(() => {
          dispatch(
            showInfoDialog({
              title: 'Reclustering Completed',
              message:
                response.message ||
                'Global face reclustering completed successfully.',
              variant: 'info',
            }),
          );
        }, 50);
      } else {
        setTimeout(() => {
          dispatch(
            showInfoDialog({
              title: 'Reclustering Failed',
              message:
                response.message ||
                'Failed to complete global face reclustering.',
              variant: 'error',
            }),
          );
        }, 50);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);

      dispatch(hideLoader());
      setTimeout(() => {
        dispatch(
          showInfoDialog({
            title: 'Reclustering Error',
            message: `Failed to start global reclustering: ${errorMessage}`,
            variant: 'error',
          }),
        );
      }, 50);
    }
  };

  const onCheckUpdatesClick = () => {
    const checkUpdates = async () => {
      dispatch(showLoader('Checking for updates...'));

      try {
        const hasUpdate = await checkForUpdates();

        if (hasUpdate) {
          // First hide the loader, then show the update dialog
          dispatch(hideLoader());
          // Add small delay to prevent UI flicker
          setTimeout(() => setUpdateDialogOpen(true), 50);
        } else {
          // First hide the loader, then show the info dialog with a small delay
          dispatch(hideLoader());
          // Add small delay to prevent UI flicker
          setTimeout(() => {
            dispatch(
              showInfoDialog({
                title: 'No Updates Available',
                message:
                  'Your application is already up to date with the latest version.',
                variant: 'info',
              }),
            );
          }, 50);
        }
      } catch (err: unknown) {
        // Handle errors during update check
        const errorMessage = err instanceof Error ? err.message : String(err);

        // First hide the loader, then show the error dialog with a small delay
        dispatch(hideLoader());
        // Add small delay to prevent UI flicker
        setTimeout(() => {
          dispatch(
            showInfoDialog({
              title: 'Error Checking Updates',
              message: errorMessage,
              variant: 'error',
            }),
          );
        }, 50);
      } finally {
        // We've moved the hideLoader calls into each specific branch to control timing
        // This empty finally block is kept for clarity and potential future use
      }
    };

    checkUpdates();
  };

  return (
    <>
      <SettingsCard
        icon={SettingsIcon}
        title="Application Controls"
        description="Manage updates, server operations, and face clustering"
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Button
            onClick={onCheckUpdatesClick}
            variant="outline"
            className="flex h-12 w-full gap-3"
          >
            <RefreshCw className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <div className="text-left">
              <div className="font-medium">Check for Updates</div>
            </div>
          </Button>

          <Button
            onClick={() => restartServer()}
            variant="outline"
            className="flex h-12 w-full gap-3"
          >
            <Server className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <div className="text-left">
              <div className="font-medium">Restart Server</div>
            </div>
          </Button>

          <Button
            onClick={onGlobalReclusterClick}
            variant="outline"
            className="flex h-12 w-full gap-3"
            title="Rebuild all face clusters from scratch using latest clustering algorithms"
          >
            <Users className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <div className="text-left">
              <div className="font-medium">Recluster Faces</div>
            </div>
          </Button>
        </div>
      </SettingsCard>

      <UpdateDialog
        update={updateAvailable}
        open={updateDialogOpen}
        onOpenChange={(open: boolean) => {
          if (!open && !isDownloading) {
            setUpdateDialogOpen(open);
            setTimeout(dismissUpdate, 1000);
          }
        }}
        onDownload={downloadAndInstall}
        onLater={() => {
          setUpdateDialogOpen(false);
          setTimeout(dismissUpdate, 1000);
        }}
        isDownloading={isDownloading}
        downloadProgress={downloadProgress}
        error={error}
        showCloseButton={false || !isDownloading}
      />
    </>
  );
};

export default ApplicationControlsCard;
