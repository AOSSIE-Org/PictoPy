import './App.css';
import React from 'react';
import { BrowserRouter } from 'react-router';
import { AppRoutes } from '@/routes/AppRoutes';
import { ThemeProvider } from '@/contexts/ThemeContext';
import QueryClientProviders from '@/config/QueryClientProvider';
import { GlobalLoader } from './components/Loader/GlobalLoader';
import GlobalInfoDialog from './components/InfoDialog/GlobalInfoDialog';
import { useSelector } from 'react-redux';
import { RootState } from './app/store';

const App: React.FC = () => {
  const { loading, message } = useSelector((state: RootState) => state.loader);

  return (
    <ThemeProvider>
      <QueryClientProviders>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
        <GlobalLoader loading={loading} message={message} />
        <GlobalInfoDialog />
      </QueryClientProviders>
    </ThemeProvider>
  );
};

export default App;
