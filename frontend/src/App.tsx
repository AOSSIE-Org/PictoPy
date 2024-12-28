import './App.css';
import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AppRoutes } from './routes/AppRoutes';
import { ThemeProvider } from './contexts/ThemeContext';

const App: React.FC = () => (
  <ThemeProvider>
    <Router>
      <AppRoutes />
    </Router>
  </ThemeProvider>
);

export default App;
