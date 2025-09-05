/**
 * Application Routes Configuration
 * 
 * This module defines the main routing structure for the PictoPy frontend application.
 * It uses React Router to handle navigation between different pages and features.
 * 
 * Route Structure:
 * - Initial Steps: Landing/onboarding page (index route)
 * - Layout Routes: All main application pages wrapped in the main layout
 *   - Home: Main gallery view
 *   - AI Tagging: AI-powered image analysis and tagging
 *   - Person Images: Face clustering and person-based image organization
 *   - Albums: Album management and creation
 *   - Settings: Application configuration
 *   - Videos: Video management (placeholder)
 *   - Memories: Memory-based organization (placeholder)
 * 
 * @component
 * @returns {JSX.Element} The configured route structure
 */

// React imports
import React from 'react';
import { Routes, Route } from 'react-router';

// Application imports
import { ROUTES } from '@/constants/routes';
import Layout from '@/layout/layout';

// Page components
import { InitialSteps } from '@/pages/InitialSteps/InitialSteps';
import Settings from '@/pages/SettingsPage/Settings';
import { Home } from '@/pages/Home/Home';
import { AITagging } from '@/pages/AITagging/AITagging';
import { PersonImages } from '@/pages/PersonImages/PersonImages';

/**
 * Main application routes component
 * 
 * Defines the routing structure for the entire PictoPy application.
 * Routes are organized with the initial steps as the landing page and
 * all other routes wrapped in the main application layout.
 */
export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Landing/onboarding page - shown when users first visit the app */}
      <Route index element={<InitialSteps />} />
      
      {/* Main application routes wrapped in the layout component */}
      <Route element={<Layout />}>
        {/* Main gallery view showing all images */}
        <Route path={ROUTES.HOME} element={<Home />} />
        
        {/* Video management page (currently using Settings component) */}
        <Route path={ROUTES.VIDEOS} element={<Settings />} />
        
        {/* Application settings and configuration */}
        <Route path={ROUTES.SETTINGS} element={<Settings />} />
        
        {/* AI-powered image tagging and analysis */}
        <Route path={ROUTES.AI} element={<AITagging />} />
        
        {/* Album management and creation */}
        <Route path={ROUTES.ALBUMS} element={<Settings />} />
        
        {/* Memory-based image organization (currently using Settings component) */}
        <Route path={ROUTES.MEMORIES} element={<Settings />} />
        
        {/* Person-based image organization using face clustering */}
        <Route path={ROUTES.PERSON} element={<PersonImages />} />
      </Route>
    </Routes>
  );
};
