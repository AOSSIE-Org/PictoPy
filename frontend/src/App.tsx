import './App.css';
import React, { useEffect } from 'react';
import { BrowserRouter } from 'react-router';
import { AppRoutes } from '@/routes/AppRoutes';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { GlobalLoader } from './components/Loader/GlobalLoader';
import { InfoDialog } from './components/Dialog/InfoDialog';
import { useSelector } from 'react-redux';
import { RootState } from './app/store';
import { startWebSocket } from '@/lib/ws';

const App: React.FC = () => {
  const { loading, message } = useSelector((state: RootState) => state.loader);
  const {
    isOpen,
    title,
    message: infoMessage,
    variant,
    showCloseButton,
  } = useSelector((state: RootState) => state.infoDialog);
  const [queryClient] = React.useState(() => new QueryClient());
  useEffect(() => {
    startWebSocket();
  }, []);
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
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
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default App;
