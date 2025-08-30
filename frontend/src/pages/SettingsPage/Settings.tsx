import React, { useEffect, useState } from 'react';
import {
  Trash2,
  Server,
  RefreshCw,
  Folder,
  Settings as SettingsIcon,
} from 'lucide-react';

import FolderPicker from '@/components/FolderPicker/FolderPicker';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import UpdateDialog from '@/components/Updater/UpdateDialog';

import { restartServer } from '@/utils/serverUtils';

import { useUpdater } from '@/hooks/useUpdater';

import { useDispatch, useSelector } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectAllFolders } from '@/features/folderSelectors';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import {
  enableAITagging,
  getAllFolders,
  disableAITagging,
  deleteFolders,
} from '@/api/api-functions';
import { setFolders } from '@/features/folderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { FolderDetails } from '@/types/Folder';

const Settings: React.FC = () => {
  const dispatch = useDispatch();

  const folders = useSelector(selectAllFolders);

  const {
    data: foldersData,
    isLoading: foldersLoading,
    isSuccess: foldersSuccess,
    isError: foldersError,
  } = usePictoQuery({
    queryKey: ['folders'],
    queryFn: getAllFolders,
  });

  const {
    mutate: enableAITaggingMutate,
    isSuccess: enableAITaggingSuccess,
    isError: enableAITaggingError,
    isPending: enableAITaggingPending,
  } = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      enableAITagging({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });
  const {
    mutate: disableAITaggingMutate,
    isSuccess: disableAITaggingSuccess,
    isError: disableAITaggingError,
    isPending: disableAITaggingPending,
  } = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      disableAITagging({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });
  const {
    mutate: deleteFolderMutate,
    isSuccess: deleteFolderSuccess,
    isError: deleteFolderError,
    isPending: deleteFolderPending,
  } = usePictoMutation({
    mutationFn: async (folder_id: string) =>
      deleteFolders({ folder_ids: [folder_id] }),
    autoInvalidateTags: ['folders'],
  });

  useEffect(() => {
    if (foldersLoading) {
      dispatch(showLoader('Loading folders'));
    } else if (foldersError) {
      dispatch(hideLoader());
    } else if (foldersSuccess) {
      const folders = foldersData?.data?.folders as FolderDetails[];
      dispatch(setFolders(folders));
      dispatch(hideLoader());
    }
  }, [foldersData, foldersSuccess, foldersError, foldersLoading, dispatch]);

  useEffect(() => {
    if (enableAITaggingPending) {
      console.log('Enabling AI tagging...');
    } else if (enableAITaggingSuccess) {
      console.log('AI tagging enabled successfully');
    } else if (enableAITaggingError) {
      console.error('Error enabling AI tagging');
    }
  }, [enableAITaggingSuccess, enableAITaggingError, enableAITaggingPending]);

  useEffect(() => {
    if (disableAITaggingPending) {
      console.log('Disabling AI tagging...');
    } else if (disableAITaggingSuccess) {
      console.log('AI tagging disabled successfully');
    } else if (disableAITaggingError) {
      console.error('Error disabling AI tagging');
    }
  }, [disableAITaggingSuccess, disableAITaggingError, disableAITaggingPending]);

  useEffect(() => {
    if (deleteFolderPending) {
      console.log('Deleting folder...');
    } else if (deleteFolderSuccess) {
      console.log('Folder deleted successfully');
    } else if (deleteFolderError) {
      console.error('Error deleting folder');
    }
  }, [deleteFolderSuccess, deleteFolderError, deleteFolderPending]);

  const handleToggleAITagging = (folder: FolderDetails) => {
    if (folder.AI_Tagging) {
      disableAITaggingMutate(folder.folder_id);
    } else {
      enableAITaggingMutate(folder.folder_id);
    }
  };

  const handleDeleteFolder = (folderId: string) => {
    deleteFolderMutate(folderId);
  };

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

  const onCheckUpdatesClick = () => {
    let checkUpdates = async () => {
      dispatch(showLoader('Checking for updates...'));
      const hasUpdate = await checkForUpdates();
      if (hasUpdate) {
        setUpdateDialogOpen(true);
      } else {
        // Show info dialog when no updates are available
        dispatch(
          showInfoDialog({
            title: 'No Updates Available',
            message:
              'Your application is already up to date with the latest version.',
            variant: 'info',
          }),
        );
      }
      dispatch(hideLoader());
    };
    checkUpdates();
  };

  return (
    <div className="mx-auto flex-1 px-8 py-6">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Folder Management Card */}
        <div className="bg-card rounded-xl border p-6 shadow-sm">
          <div className="border-border mb-6 flex items-center gap-3 border-b pb-4">
            <Folder className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <div>
              <h2 className="text-card-foreground text-lg font-medium">
                Folder Management
              </h2>
              <p className="text-muted-foreground text-sm">
                Configure your photo library folders and AI settings
              </p>
            </div>
          </div>

          {folders.length > 0 ? (
            <div className="space-y-3">
              {folders.map((folder, index) => (
                <div
                  key={index}
                  className="group border-border bg-background/50 relative rounded-lg border p-4 transition-all hover:border-gray-300 hover:shadow-sm dark:hover:border-gray-600"
                >
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-3">
                        <Folder className="h-4 w-4 flex-shrink-0 text-gray-500 dark:text-gray-400" />
                        <span className="text-foreground truncate">
                          {folder.folder_path}
                        </span>
                      </div>
                    </div>

                    <div className="ml-4 flex items-center gap-4">
                      <div className="flex items-center gap-3">
                        <span className="text-muted-foreground text-sm">
                          AI Tagging
                        </span>
                        <Switch
                          checked={folder.AI_Tagging}
                          onCheckedChange={() => handleToggleAITagging(folder)}
                          disabled={
                            enableAITaggingPending || disableAITaggingPending
                          }
                        />
                      </div>

                      <Button
                        onClick={() => handleDeleteFolder(folder.folder_id)}
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 text-gray-500 hover:border-red-300 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                        disabled={deleteFolderPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center">
              <Folder className="mx-auto mb-3 h-12 w-12 text-gray-400" />
              <h3 className="text-foreground mb-1 text-lg font-medium">
                No folders configured
              </h3>
              <p className="text-muted-foreground text-sm">
                Add your first photo library folder to get started
              </p>
            </div>
          )}

          <div className="border-border mt-6 border-t pt-6">
            <FolderPicker />
          </div>
        </div>

        {/* Application Controls Card */}
        <div className="bg-card rounded-xl border p-6 shadow-sm">
          <div className="border-border mb-6 flex items-center gap-3 border-b pb-4">
            <SettingsIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <div>
              <h2 className="text-card-foreground text-lg font-medium">
                Application Controls
              </h2>
              <p className="text-muted-foreground text-sm">
                Manage updates and server operations
              </p>
            </div>
          </div>

          <div className="flex w-50 gap-4">
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

            {true && (
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
            )}
          </div>
        </div>
      </div>
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
    </div>
  );
};

export default Settings;
