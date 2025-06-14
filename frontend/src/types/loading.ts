export interface LoadingContextType {
  isLoading: boolean;
  loadingMessage: string;
  showLoader: (message?: string) => void;
  hideLoader: () => void;
}
export interface GlobalLoaderProps {
  message: string;
}
