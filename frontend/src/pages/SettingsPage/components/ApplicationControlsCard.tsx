import React, { useState } from 'react';
import { Settings as SettingsIcon, RefreshCw, Users } from 'lucide-react';

import { Button } from '@/components/ui/button';
import UpdateDialog from '@/components/Updater/UpdateDialog';
import SettingsCard from './SettingsCard';

import { useUpdater } from '@/hooks/useUpdater';
import { useDispatch } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { triggerGlobalReclustering } from '@/api/api-functions/face_clusters';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

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

  const reclusterMutation = usePictoMutation({
    mutationFn: triggerGlobalReclustering,
    autoInvalidateTags: ['clusters'],
  });

  const feedbackOptions = React.useMemo(
    () => ({
      loadingMessage: 'Starting global face reclustering...',
      successTitle: 'Reclustering Completed',
      successMessage:
        reclusterMutation.successMessage ||
        'Global face reclustering completed successfully.',
      errorTitle: 'Reclustering Failed',
      errorMessage:
        reclusterMutation.errorMessage ||
        'Failed to complete global face reclustering.',
      // You can use reclusterMutation.successData?.clusters_created to show the number of clusters created if needed
      // Example: `Clusters created: ${reclusterMutation.successData?.clusters_created}`
    }),
    [
      reclusterMutation.successMessage,
      reclusterMutation.errorMessage,
      reclusterMutation.successData,
    ],
  );

  useMutationFeedback(reclusterMutation, feedbackOptions);

  const onGlobalReclusterClick = () => {
    reclusterMutation.mutate(undefined);
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
            className="flex h-12 w-full cursor-pointer gap-3"
          >
            <RefreshCw className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <div className="text-left">
              <div className="font-medium">Check for Updates</div>
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
