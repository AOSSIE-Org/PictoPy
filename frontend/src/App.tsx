import './App.css';
import React from 'react';
import { BrowserRouter } from 'react-router';
import { AppRoutes } from '@/routes/AppRoutes';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import QueryClientProviders from '@/config/QueryClientProvider';
import { QueryErrorResetBoundary } from '@tanstack/react-query';
import { GlobalLoader } from './components/Loader/GlobalLoader';
import { InfoDialog } from './components/Dialog/InfoDialog';
import { useSelector } from 'react-redux';
import { RootState } from './app/store';
const App: React.FC = () => {
  const { loading, message } = useSelector((state: RootState) => state.loader);
  const {
    isOpen,
    title,
    message: infoMessage,
    variant,
    showCloseButton,
  } = useSelector((state: RootState) => state.infoDialog);
  return (
    <ThemeProvider>
      <QueryClientProviders>
        <QueryErrorResetBoundary>
          {({ reset }) => (
            <ErrorBoundary onRetry={reset}>
              <BrowserRouter>
                <AppRoutes />
              </BrowserRouter>
              <GlobalLoader loading={loading} message={message} />
              <InfoDialog
                isOpen={isOpen}
                title={title}
                message={infoMessage}
                variant={variant}
                showCloseButton={showCloseButton}
              />
            </ErrorBoundary>
          )}
        </QueryErrorResetBoundary>
      </QueryClientProviders>
    </ThemeProvider>
  );
};

export default App;
