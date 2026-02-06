import './App.css';
import React from 'react';
import { BrowserRouter } from 'react-router';
import { AppRoutes } from '@/routes/AppRoutes';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import QueryClientProviders from '@/config/QueryClientProvider';
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
      <ErrorBoundary>
        <QueryClientProviders>
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
        </QueryClientProviders>
      </ErrorBoundary>
    </ThemeProvider>
  );
};

export default App;
