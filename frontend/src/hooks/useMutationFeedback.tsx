import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';

type MutationState = {
  isPending?: boolean;
  isSuccess?: boolean;
  isError?: boolean;
  error?: Error | unknown;
  errorMessage?: string;
};

type FeedbackOptions = {
  /**
   * Show loading state
   */
  showLoading?: boolean;
  /**
   * Custom loading message
   */
  loadingMessage?: string;
  /**
   * Show success message
   */
  showSuccess?: boolean;
  /**
   * Custom success title
   */
  successTitle?: string;
  /**
   * Custom success message
   */
  successMessage?: string;
  /**
   * Show error message
   */
  showError?: boolean;
  /**
   * Custom error title
   */
  errorTitle?: string;
  /**
   * Custom error message
   */
  errorMessage?: string;
  /**
   * Optional callback on success
   */
  onSuccess?: () => void;
  /**
   * Optional callback on error
   */
  onError?: (error: Error | unknown) => void;
};

/**
 * Custom hook to provide standardized feedback for mutation states
 * Handles loading indicators, success messages, and error messages
 */
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

  const { isPending, isSuccess, isError, error, errorMessage: stateErrorMessage } = mutationState;

  const isShowingLoaderRef = useRef(false);
  const hasHandledSuccessRef = useRef(false);
  const lastShownErrorMsg = useRef<string | null>(null);

  const onSuccessRef = useRef(onSuccess);
  onSuccessRef.current = onSuccess;

  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;

  // Handle loading state
  useEffect(() => {
    if (showLoading && isPending) {
      isShowingLoaderRef.current = true;
      dispatch(showLoader(loadingMessage));
    } else if (!isPending && isShowingLoaderRef.current) {
      isShowingLoaderRef.current = false;
      dispatch(hideLoader());
    }
  }, [isPending, showLoading, loadingMessage, dispatch]);

  // Cleanup on unmount if loader was triggered
  useEffect(() => {
    return () => {
      if (isShowingLoaderRef.current) {
        dispatch(hideLoader());
      }
    };
  }, [dispatch]);

  // Clear handled success flag when mutation is no longer in success state
  useEffect(() => {
    if (!isSuccess) {
      hasHandledSuccessRef.current = false;
    }
  }, [isSuccess]);

  // Handle success state
  useEffect(() => {
    if (isSuccess && !hasHandledSuccessRef.current) {
      hasHandledSuccessRef.current = true;

      if (showSuccess) {
        dispatch(
          showInfoDialog({
            title: successTitle,
            message: successMessage,
            variant: 'info',
          }),
        );
      }

      if (onSuccessRef.current) {
        onSuccessRef.current();
      }
    }
  }, [
    isSuccess,
    showSuccess,
    successTitle,
    successMessage,
    dispatch,
  ]);

  // Clear last shown error when error is resolved
  useEffect(() => {
    if (!isError) {
      lastShownErrorMsg.current = null;
    }
  }, [isError]);

  // Handle error state
  useEffect(() => {
    if (isError) {
      const errorMsg = stateErrorMessage || (error instanceof Error ? error.message : errorMessage);

      if (lastShownErrorMsg.current !== errorMsg) {
        lastShownErrorMsg.current = errorMsg;

        if (showError) {
          dispatch(
            showInfoDialog({
              title: errorTitle,
              message: errorMsg,
              variant: 'error',
            }),
          );
        }

        if (onErrorRef.current) {
          onErrorRef.current(error);
        }
      }
    }
  }, [isError, showError, errorTitle, errorMessage, stateErrorMessage, error, dispatch]);

  // Return original state for convenience
  return mutationState;
};

export default useMutationFeedback;
