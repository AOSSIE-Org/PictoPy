import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import {
  getMainBackendHealthStatus,
  getSyncMicroserviceHealthStatus,
} from '@/api/api-functions';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { markCompleted } from '@/features/onboardingSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { exit } from '@tauri-apps/plugin-process';

interface ServerCheckProps {
  stepIndex: number;
}
export const ServerCheck: React.FC<ServerCheckProps> = ({ stepIndex }) => {
  const dispatch = useDispatch();
  const {
    isSuccess: mainBackendSuccess,
    isLoading: mainBackendLoading,
    isError: mainBackendError,
  } = usePictoQuery({
    queryKey: ['clusters'],
    queryFn: getMainBackendHealthStatus,
    retry: 60,
    retryDelay: 1000,
  });
  const {
    isSuccess: syncMicroserviceSuccess,
    isLoading: syncMicroserviceLoading,
    isError: syncMicroserviceError,
  } = usePictoQuery({
    queryKey: ['syncMicroservice'],
    queryFn: getSyncMicroserviceHealthStatus,
    retry: 60,
    retryDelay: 1000,
  });
  useEffect(() => {
    if (mainBackendLoading || syncMicroserviceLoading) {
      dispatch(showLoader('Waiting for servers to start'));
    }
    if (mainBackendError || syncMicroserviceError) {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Error',
          message:
            'Failed to connect to one or more local services. Exiting...',
          variant: 'error',
          showCloseButton: false,
        }),
      );
      setTimeout(() => {
        exit(1);
      }, 2000);
    }
    if (mainBackendSuccess && syncMicroserviceSuccess) {
      dispatch(hideLoader());
      dispatch(markCompleted(stepIndex));
    }
  }, [
    mainBackendSuccess,
    mainBackendLoading,
    mainBackendError,
    syncMicroserviceSuccess,
    syncMicroserviceLoading,
    syncMicroserviceError,
  ]);
  return null;
};
