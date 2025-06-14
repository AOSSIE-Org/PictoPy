// src/hooks/useLoading.ts
import { useContext } from 'react';
import { LoadingContext } from '../contexts/LoadingContext';
import { LoadingContextType } from '../types/loading.ts';

export const useLoading = (): LoadingContextType => {
  const context = useContext(LoadingContext);

  if (!context) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }

  return context;
};
