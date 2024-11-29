import { ROUTES } from '@/constants/routes';
import AITagging from '@/pages/AITagging/AITaging';
import Album from '@/pages/Album/Album';
import Dashboard from '@/pages/Dashboard/Dashboard';
import Settings from '@/pages/SettingsPage/Settings';
import Videos from '@/pages/VideosPage/Videos';

import React from 'react';
import { Routes, Route } from 'react-router-dom';

export const LayoutRoutes: React.FC = () => (
  <Routes>
    <Route path={ROUTES.LAYOUT.HOME} element={<Dashboard />} />
    <Route path={ROUTES.LAYOUT.VIDEOS} element={<Videos />} />
    <Route path={ROUTES.LAYOUT.SETTINGS} element={<Settings />} />
    <Route path={ROUTES.LAYOUT.AI} element={<AITagging />} />
    <Route path={ROUTES.LAYOUT.ALBUM} element={<Album />} />
  </Routes>
);
