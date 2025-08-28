import './App.css';
import React from 'react';
import { BrowserRouter } from 'react-router';
import { AppRoutes } from '@/routes/AppRoutes';
import { ThemeProvider } from '@/contexts/ThemeContext';
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
  } = useSelector((state: RootState) => state.infoDialog);
  return (
    <ThemeProvider>
      <QueryClientProviders>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
        <GlobalLoader loading={loading} message={message} />
        <InfoDialog isOpen={isOpen} title={title} message={infoMessage} />
      </QueryClientProviders>
    </ThemeProvider>
  );
};

export default App;
