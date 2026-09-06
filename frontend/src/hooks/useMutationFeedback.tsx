import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { getErrorMessage } from '@/lib/utils';

type MutationState = {
  isPending?: boolean;
  isSuccess?: boolean;
  isError?: boolean;
  error?: Error | unknown;
};

type FeedbackOptions = {
  showLoading?: boolean;
  loadingMessage?: string;
  showSuccess?: boolean;
  successTitle?: string;
  successMessage?: string;
  showError?: boolean;
  errorTitle?: string;
  errorMessage?: string;
  onSuccess?: () => void;
  onError?: (error: Error | unknown) => void;
};

export const useMutationFeedback = (
  mutationState: MutationState,
  options: FeedbackOptions = {},
) => {
  const dispatch = useDispatch();

  const {
    showLoading = true,
    loadingMessage = 'Processing...',
    showSuccess = true,
    successTitle = 'Success',
    successMessage = 'Operation completed successfully.',
    showError = true,
    errorTitle = 'Error',
    errorMessage = 'An error occurred. Please try again.',
    onSuccess,
    onError,
  } = options;

  // Held in refs so an inline callback, which is a new function every render,
  // stays out of the effect deps below and cannot re-fire the dialog.
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  onSuccessRef.current = onSuccess;
  onErrorRef.current = onError;

  const { isPending, isSuccess, isError, error } = mutationState;

  useEffect(() => {
    if (showLoading && isPending) {
      dispatch(showLoader(loadingMessage));
    } else if (!isPending) {
      dispatch(hideLoader());
    }
  }, [isPending, showLoading, loadingMessage, dispatch]);

  useEffect(() => {
    if (isSuccess && showSuccess) {
      dispatch(
        showInfoDialog({
          title: successTitle,
          message: successMessage,
          variant: 'info',
        }),
      );

      if (onSuccessRef.current) {
        onSuccessRef.current();
      }
    }
  }, [isSuccess, showSuccess, successTitle, successMessage, dispatch]);

  useEffect(() => {
    if (isError && showError) {
      const errorMsg = getErrorMessage(error, errorMessage);

      dispatch(
        showInfoDialog({
          title: errorTitle,
          message: errorMsg,
          variant: 'error',
        }),
      );

      if (onErrorRef.current) {
        onErrorRef.current(error);
      }
    }
  }, [isError, showError, errorTitle, errorMessage, error, dispatch]);

  return mutationState;
};

export default useMutationFeedback;
