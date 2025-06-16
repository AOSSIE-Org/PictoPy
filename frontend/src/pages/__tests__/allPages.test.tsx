import { render } from '@testing-library/react';
import AITagging from '../AITagging/AITagging';
import Album from '../Album/Album';
import Dashboard from '../Dashboard/Dashboard';
import Memories from '../Memories/Memories';
import SecureFolder from '../SecureFolderPage/SecureFolder';
import Settings from '../SettingsPage/Settings';
import Videos from '../VideosPage/Videos';
import { ROUTES } from '@/constants/routes';
import QueryClientProviders from '@/config/QueryClientProvider';
import { BrowserRouter } from 'react-router';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LoadingProvider } from '@/contexts/LoadingContext';

beforeAll(() => {
  window.matchMedia =
    window.matchMedia ||
    function () {
      return {
        matches: false,
        addListener: () => {}, // deprecated
        removeListener: () => {}, // deprecated
      };
    };
});

const pages = [
  { path: ROUTES.LAYOUT.HOME, Component: Dashboard },
  { path: ROUTES.LAYOUT.VIDEOS, Component: Videos },
  { path: ROUTES.LAYOUT.SETTINGS, Component: Settings },
  { path: ROUTES.LAYOUT.AI, Component: AITagging },
  { path: ROUTES.LAYOUT.ALBUMS, Component: Album },
  { path: ROUTES.LAYOUT.SECURE_FOLDER, Component: SecureFolder },
  { path: ROUTES.LAYOUT.MEMORIES, Component: Memories },
];

describe('Page rendering tests', () => {
  pages.forEach(({ path, Component }) => {
    test(`renders ${path} without crashing`, () => {
      render(
        <ThemeProvider>
          <QueryClientProviders>
            <BrowserRouter>
              <LoadingProvider>
                <Component />
              </LoadingProvider>
            </BrowserRouter>
          </QueryClientProviders>
        </ThemeProvider>,
      );
    });
  });
});
