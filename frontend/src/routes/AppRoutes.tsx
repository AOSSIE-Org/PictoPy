import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';

import { ROUTES } from '../constants/routes';
import Layout from '@/layout/main';
import { LayoutRoutes } from './LayoutRoutes/LayoutRoutes';
import { InitialPage } from '@/pages/Setupscreen/Setup';

export const AppRoutes: React.FC = () => {
  const location = useLocation();
  const isLayoutRoute = Object.values(ROUTES.LAYOUT).includes(
    location.pathname,
  );

  return (
    <>
      <Routes>
        <Route path={ROUTES.INITIAL} element={<InitialPage />} />
      </Routes>
      {isLayoutRoute && (
        <Layout>
          <LayoutRoutes />
        </Layout>
      )}
    </>
  );
};
