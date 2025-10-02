import { AlbumDetail } from '@/components/Album/AlbumDetail';
import { ROUTES } from '@/constants/routes';
import Layout from '@/layout/layout';
import { AITagging } from '@/pages/AITagging/AITagging';
import Album from '@/pages/Album/Album';
import { ComingSoon } from '@/pages/ComingSoon/ComingSoon';
import { Home } from '@/pages/Home/Home';
import { InitialSteps } from '@/pages/InitialSteps/InitialSteps';
import { PersonImages } from '@/pages/PersonImages/PersonImages';
import Settings from '@/pages/SettingsPage/Settings';
import { Route, Routes } from 'react-router';

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
