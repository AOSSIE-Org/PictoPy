import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';

type MutationState = {
  isPending?: boolean;
  isSuccess?: boolean;
  isError?: boolean;
  error?: Error | unknown;
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

  const { isPending, isSuccess, isError, error } = mutationState;

  // Handle loading state
  useEffect(() => {
    if (showLoading && isPending) {
      dispatch(showLoader(loadingMessage));
    } else if (!isPending) {
      dispatch(hideLoader());
    }
  }, [isPending, showLoading, loadingMessage, dispatch]);

  // Handle success state
  useEffect(() => {
    if (isSuccess && showSuccess) {
      dispatch(
        showInfoDialog({
          title: successTitle,
          message: successMessage,
          variant: 'info',
        }),
      );

      if (onSuccess) {
        onSuccess();
      }
    }
  }, [
    isSuccess,
    showSuccess,
    successTitle,
    successMessage,
    dispatch,
    onSuccess,
  ]);

  // Handle error state
  useEffect(() => {
    if (isError && showError) {
      const errorMsg = error instanceof Error ? error.message : errorMessage;

      dispatch(
        showInfoDialog({
          title: errorTitle,
          message: errorMsg,
          variant: 'error',
        }),
      );

      if (onError) {
        onError(error);
      }
    }
  }, [isError, showError, errorTitle, errorMessage, error, dispatch, onError]);

  // Return original state for convenience
  return mutationState;
};

export default useMutationFeedback;
