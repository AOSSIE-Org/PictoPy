import './App.css';
import React from 'react';
import { BrowserRouter } from 'react-router';
import { AppRoutes } from '@/routes/AppRoutes';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LoadingProvider } from '@/contexts/LoadingContext';
import QueryClientProviders from '@/config/QueryClientProvider';
const App: React.FC = () => {
  return (
    <ThemeProvider>
      <QueryClientProviders>
        <LoadingProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </LoadingProvider>
      </QueryClientProviders>
    </ThemeProvider>
  );
};

export default App;
