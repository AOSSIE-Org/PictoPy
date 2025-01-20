import './App.css';
import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AppRoutes } from './routes/AppRoutes';
import { ThemeProvider } from './contexts/ThemeContext';
import QueryClientProviders from './Config/QueryClientProvider';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { serverInterface } from './hooks/serverInterface';
import { isProd } from '@/utils/isProd';
const App: React.FC = () => {
  //Listen for window close event and stop server
  const onCloseListener = async () => {
    await getCurrentWindow().onCloseRequested(async () => {
      const { stopServer } = serverInterface();
      await stopServer();
    });
  };
  useEffect(() => {
    //Run FastAPI server only when in production mode
    if (isProd()) {
      onCloseListener();
      const { startServer } = serverInterface();
      console.log('Starting PictoPy Server');
      startServer();
    }
  }, []);
  return (
    <ThemeProvider>
      <QueryClientProviders>
        <Router>
          <AppRoutes />
        </Router>
      </QueryClientProviders>
    </ThemeProvider>
  );
};

export default App;
