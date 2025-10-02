
import { Routes, Route } from 'react-router';
import { ROUTES } from '@/constants/routes';
import Layout from '@/layout/layout';
import { InitialSteps } from '@/pages/InitialSteps/InitialSteps';
import Settings from '@/pages/SettingsPage/Settings';
import { Home } from '@/pages/Home/Home';
import { AITagging } from '@/pages/AITagging/AITagging';
import { PersonImages } from '@/pages/PersonImages/PersonImages';
import { ComingSoon } from '@/pages/ComingSoon/ComingSoon';
import Album from '@/pages/Album/Album';
import { AlbumDetail } from '@/components/Album/AlbumDetail';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route index element={<InitialSteps />} />
      <Route element={<Layout />}>
        <Route path={ROUTES.HOME} element={<Home />} />
        <Route path={ROUTES.VIDEOS} element={<ComingSoon />} />
        <Route path={ROUTES.SETTINGS} element={<Settings />} />
        <Route path={ROUTES.AI} element={<AITagging />} />
        <Route path={ROUTES.ALBUMS} element={<Album />} />
        <Route path={ROUTES.ALBUM_DETAIL} element={<AlbumDetail />} />
        <Route path={ROUTES.MEMORIES} element={<ComingSoon />} />
        <Route path={ROUTES.PERSON} element={<PersonImages />} />
      </Route>
    </Routes>
  );
};
