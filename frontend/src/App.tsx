/**
 * PictoPy Frontend Main Application Component
 * 
 * This is the root component of the PictoPy frontend application. It sets up
 * the application's core providers and renders the main UI components.
 * 
 * The App component provides:
 * - Theme management (light/dark mode)
 * - React Query for API state management
 * - React Router for navigation
 * - Global loading states
 * - Information dialogs for user feedback
 * 
 * @component
 * @returns {JSX.Element} The main application component
 */

// Import styles
import './App.css';

// React imports
import React from 'react';
import { BrowserRouter } from 'react-router';
import { useSelector } from 'react-redux';

// Application imports
import { AppRoutes } from '@/routes/AppRoutes';
import { ThemeProvider } from '@/contexts/ThemeContext';
import QueryClientProviders from '@/config/QueryClientProvider';
import { GlobalLoader } from './components/Loader/GlobalLoader';
import { InfoDialog } from './components/Dialog/InfoDialog';
import { useSelector } from 'react-redux';
import { RootState } from './app/store';

/**
 * Main App component that renders the entire PictoPy application
 */
const App: React.FC = () => {
  // Extract loading state from Redux store
  const { loading, message } = useSelector((state: RootState) => state.loader);
  
  // Extract info dialog state from Redux store
  const {
    isOpen,
    title,
    message: infoMessage,
    variant,
  } = useSelector((state: RootState) => state.infoDialog);

  return (
    <ThemeProvider>
      <QueryClientProviders>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
        {/* Global loading indicator */}
        <GlobalLoader loading={loading} message={message} />
        {/* Information dialog for user feedback */}
        <InfoDialog
          isOpen={isOpen}
          title={title}
          message={infoMessage}
          variant={variant}
        />
      </QueryClientProviders>
    </ThemeProvider>
  );
};

export default App;
