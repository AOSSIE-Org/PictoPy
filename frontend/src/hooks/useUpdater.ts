import { useState, useCallback } from 'react';
import { Update, check } from '@tauri-apps/plugin-updater';
import { isTauriEnvironment } from '@/utils/tauriUtils';
import logger from '@/utils/logger';

interface DownloadProgress {
  downloaded: number;
  total: number;
}

interface UseUpdaterReturn {
  // State
  updateAvailable: Update | null;
  isDownloading: boolean;
  downloadProgress: DownloadProgress;
  error: string | null;

  // Functions
  checkForUpdates: () => Promise<boolean>;
  downloadAndInstall: () => Promise<void>;
  dismissUpdate: () => void;
  resetState: () => void;
}

export const useUpdater = (): UseUpdaterReturn => {
  const [updateAvailable, setUpdateAvailable] = useState<Update | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress>({
    downloaded: 0,
    total: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const checkForUpdates = useCallback(async (): Promise<boolean> => {
    setError(null);

    // Skip update check in browser mode (though this shouldn't happen with BrowserWarning)
    if (!isTauriEnvironment()) {
      logger.info('Skipping update check in browser mode');
      return false;
    }

    try {
      logger.info('Checking for updates...');
      const update = await check();

      if (update) {
        logger.info(
          `Found update ${update.version} from ${update.date} with notes ${update.body}`,
        );
        setUpdateAvailable(update);
        return true;
      } else {
        logger.info('No updates available');
        return false;
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to check for updates';
      logger.error('Error checking for updates:', err);
      setError(errorMessage);
      return false;
    }
  }, []);

  const downloadAndInstall = useCallback(async (): Promise<void> => {
    if (!updateAvailable) {
      logger.warn('No update available to download');
      return;
    }

    if (!isTauriEnvironment()) {
      logger.warn('Update download is not available in browser mode');
      return;
    }

    setIsDownloading(true);
    setDownloadProgress({ downloaded: 0, total: 0 });
    setError(null);

    try {
      await updateAvailable.downloadAndInstall((event) => {
        switch (event.event) {
          case 'Started':
            const contentLength = event.data.contentLength || 0;
            setDownloadProgress((prev) => ({ ...prev, total: contentLength }));
            logger.info(`Started downloading ${contentLength} bytes`);
            break;
          case 'Progress':
            setDownloadProgress((prev) => ({
              ...prev,
              downloaded: prev.downloaded + event.data.chunkLength,
            }));
            break;
          case 'Finished':
            logger.info('Download finished');
            break;
        }
      });

      logger.info('Update installed successfully');
      // The app will restart automatically after installation
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to download update';
      logger.error('Error downloading update:', err);
      setError(errorMessage);
      setIsDownloading(false);
    }
  }, [updateAvailable]);

  const dismissUpdate = useCallback(() => {
    setUpdateAvailable(null);
    setIsDownloading(false);
    setDownloadProgress({ downloaded: 0, total: 0 });
    setError(null);
  }, []);

  const resetState = useCallback(() => {
    setUpdateAvailable(null);
    setIsDownloading(false);
    setDownloadProgress({ downloaded: 0, total: 0 });
    setError(null);
  }, []);

  return {
    // State
    updateAvailable,
    isDownloading,
    downloadProgress,
    error,

    // Functions
    checkForUpdates,
    downloadAndInstall,
    dismissUpdate,
    resetState,
  };
};
