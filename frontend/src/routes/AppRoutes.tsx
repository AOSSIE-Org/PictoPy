import React from 'react';
import { Routes, Route } from 'react-router';
import { ROUTES } from '@/constants/routes';
import Layout from '@/layout/layout';
import { InitialSteps } from '@/pages/InitialSteps/InitialSteps';
import Settings from '@/pages/SettingsPage/Settings';
import { Home } from '@/pages/Home/Home';
import { AITagging } from '@/pages/AITagging/AITagging';
import { PersonImages } from '@/pages/PersonImages/PersonImages';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<InitialSteps />} />
      <Route element={<Layout />}>
        <Route path={ROUTES.HOME} element={<Home />} />
        <Route path={ROUTES.VIDEOS} element={<Settings />} />
        <Route path={ROUTES.SETTINGS} element={<Settings />} />
        <Route path={ROUTES.AI} element={<AITagging />} />
        <Route path={ROUTES.ALBUMS} element={<Settings />} />
        <Route path={ROUTES.MEMORIES} element={<Settings />} />
        <Route path={ROUTES.PERSON} element={<PersonImages />} />
      </Route>
    </Routes>
  );
};
