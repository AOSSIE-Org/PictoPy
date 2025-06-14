import React from 'react';
import { Routes, Route } from 'react-router';
import Layout from '@/layout/layout';
import { InitialSteps } from '@/pages/InitialSteps/InitialSteps';
// Layout Components
import { ROUTES } from '@/constants/routes';
import AITagging from '@/pages/AITagging/AITaging';
import Album from '@/pages/Album/Album';
import Dashboard from '@/pages/Dashboard/Dashboard';
import SecureFolder from '@/pages/SecureFolderPage/SecureFolder';
import Memories from '@/pages/Memories/Memories';
import Settings from '@/pages/SettingsPage/Settings';
import Videos from '@/pages/VideosPage/Videos';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<InitialSteps />} />
      <Route element={<Layout />}>
        <Route path={ROUTES.LAYOUT.HOME} element={<Dashboard />} />
        <Route path={ROUTES.LAYOUT.VIDEOS} element={<Videos />} />
        <Route path={ROUTES.LAYOUT.SETTINGS} element={<Settings />} />
        <Route path={ROUTES.LAYOUT.AI} element={<AITagging />} />
        <Route path={ROUTES.LAYOUT.ALBUMS} element={<Album />} />
        <Route path={ROUTES.LAYOUT.SECURE_FOLDER} element={<SecureFolder />} />
        <Route path={ROUTES.LAYOUT.MEMORIES} element={<Memories />} />
      </Route>
    </Routes>
  );
};
