import './App.css';
import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AppRoutes } from './routes/AppRoutes';
import { ThemeProvider } from './contexts/ThemeContext';
import QueryClientProviders from './Config/QueryClientProvider';
const App: React.FC = () => {
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
