// src/contexts/LoadingContext.tsx
import { createContext, ReactNode, useState } from 'react';
import { LoadingContextType } from '@/types/loading.ts';
import { GlobalLoader } from '@/components/Loader/GlobalLoader';

// Create the context
export const LoadingContext = createContext<LoadingContextType | undefined>(
  undefined,
);

// Loading Provider Component
export function LoadingProvider({
  children,
}: {
  children: ReactNode;
}): JSX.Element {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');

  const showLoader = (message: string = 'Loading...'): void => {
    setLoadingMessage(message);
    setIsLoading(true);
  };

  const hideLoader = (): void => {
    setIsLoading(false);
    console.log('Loader hidden');
    setLoadingMessage('');
  };

  const value: LoadingContextType = {
    isLoading,
    loadingMessage,
    showLoader,
    hideLoader,
  };

  return (
    <LoadingContext.Provider value={value}>
      {children}
      {isLoading && <GlobalLoader message={loadingMessage} />}
    </LoadingContext.Provider>
  );
}
