import React, { useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import { hideGlobalAlert } from '@/features/globalAlertSlice';

const GlobalAlert: React.FC = () => {
  const dispatch = useDispatch();
  const { isOpen, title, message } = useSelector(
    (state: RootState) => state.globalAlert,
  );

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const timer = window.setTimeout(() => {
      dispatch(hideGlobalAlert());
    }, 5000);

    return () => window.clearTimeout(timer);
  }, [dispatch, isOpen, title, message]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="animate-in slide-in-from-bottom-5 fade-in fixed right-4 bottom-4 z-50 w-[calc(100vw-2rem)] max-w-sm duration-300">
      <Alert className="relative border-orange-200 bg-orange-50 text-orange-900 shadow-lg dark:border-orange-800 dark:bg-orange-950 dark:text-orange-100">
        <AlertCircle />
        <AlertTitle className="pr-8 text-orange-900 dark:text-orange-100">
          {title}
        </AlertTitle>
        <AlertDescription className="pr-8 text-orange-900/90 dark:text-orange-100/90">
          {message}
        </AlertDescription>
        <button
          type="button"
          aria-label="Dismiss alert"
          onClick={() => dispatch(hideGlobalAlert())}
          className="absolute top-3 right-3 inline-flex h-7 w-7 items-center justify-center rounded-md text-orange-900/70 transition-colors hover:bg-orange-100 hover:text-orange-900 dark:text-orange-100/70 dark:hover:bg-orange-900"
        >
          <X className="h-4 w-4" />
        </button>
      </Alert>
    </div>
  );
};

export default GlobalAlert;
