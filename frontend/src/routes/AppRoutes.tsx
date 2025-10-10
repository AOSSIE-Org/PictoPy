import React from 'react';
import { Routes, Route } from 'react-router';
import { ROUTES } from '@/constants/routes';
import Layout from '@/layout/layout';
import { InitialSteps } from '@/pages/InitialSteps/InitialSteps';
import Settings from '@/pages/SettingsPage/Settings';
import { Home } from '@/pages/Home/Home';
import { AITagging } from '@/pages/AITagging/AITagging';
import { PersonImages } from '@/pages/PersonImages/PersonImages';
import { ComingSoon } from '@/pages/ComingSoon/ComingSoon';
import { SearchImages } from '@/pages/SearchImages/SearchImages';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<InitialSteps />} />
      <Route element={<Layout />}>
        <Route path={ROUTES.HOME} element={<Home />} />
        <Route path={ROUTES.VIDEOS} element={<ComingSoon />} />
        <Route path={ROUTES.SETTINGS} element={<Settings />} />
        <Route path={ROUTES.AI} element={<AITagging />} />
        <Route path={ROUTES.ALBUMS} element={<ComingSoon />} />
        <Route path={ROUTES.MEMORIES} element={<ComingSoon />} />
        <Route path={ROUTES.PERSON} element={<PersonImages />} />
        <Route path={ROUTES.SEARCH} element={<SearchImages />} />
      </Route>
    </Routes>
  );
};
