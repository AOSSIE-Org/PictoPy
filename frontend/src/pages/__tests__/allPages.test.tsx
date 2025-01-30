import { render } from '@testing-library/react';
import AITagging from '../AITagging/AITaging';
import Album from '../Album/Album';
import Dashboard from '../Dashboard/Dashboard';
import Memories from '../Memories/Memories';
import SecureFolder from '../SecureFolderPage/SecureFolder';
import Settings from '../SettingsPage/Settings';
import { InitialPage } from '../Setupscreen/Setup';
import Videos from '../VideosPage/Videos';
import { ROUTES } from '@/constants/routes';
import QueryClientProviders from '@/Config/QueryClientProvider';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@/contexts/ThemeContext';

const pages = [
  { path: ROUTES.LAYOUT.HOME, Component: Dashboard },
  { path: ROUTES.LAYOUT.VIDEOS, Component: Videos },
  { path: ROUTES.LAYOUT.SETTINGS, Component: Settings },
  { path: ROUTES.LAYOUT.AI, Component: AITagging },
  { path: ROUTES.LAYOUT.ALBUM, Component: Album },
  { path: ROUTES.LAYOUT.SECURE_FOLDER, Component: SecureFolder },
  { path: ROUTES.LAYOUT.MEMORIES, Component: Memories },
  { path: ROUTES.INITIAL, Component: InitialPage },
];

describe('Page rendering tests', () => {
  pages.forEach(({ path, Component }) => {
    test(`renders ${path} without crashing`, () => {
      render(
        <ThemeProvider>
          <QueryClientProviders>
            <BrowserRouter>
              <Component />
            </BrowserRouter>
          </QueryClientProviders>
        </ThemeProvider>,
      );
    });
  });
});
