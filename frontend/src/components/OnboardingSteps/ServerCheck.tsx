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
          title: 'Connection Error',
          message:
            'Could not connect to the backend server. Please ensure the backend (Python) is running and try again.',
          variant: 'error',
          showCloseButton: true,
        }),
      );
      // Removed auto-exit to allow debugging
      // setTimeout(() => {
      //   exit(1);
      // }, 2000);
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
