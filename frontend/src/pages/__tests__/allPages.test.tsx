import { render } from '@testing-library/react';
import AITagging from '../AITagging/AITagging';
import Album from '../Album/Album';
import Dashboard from '../Home/Home';
import Memories from '../Memories/Memories';
import SecureFolder from '../SecureFolderPage/SecureFolder';
import Settings from '../SettingsPage/Settings';
import Videos from '../VideosPage/Videos';
import { ROUTES } from '@/constants/routes';
import QueryClientProviders from '@/config/QueryClientProvider';
import { BrowserRouter } from 'react-router';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { Provider } from 'react-redux';
import { store } from '@/app/store';
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
  { path: ROUTES.HOME, Component: Dashboard },
  { path: ROUTES.VIDEOS, Component: Videos },
  { path: ROUTES.SETTINGS, Component: Settings },
  { path: ROUTES.AI, Component: AITagging },
  { path: ROUTES.ALBUMS, Component: Album },
  { path: ROUTES.SECURE_FOLDER, Component: SecureFolder },
  { path: ROUTES.MEMORIES, Component: Memories },
];

describe('Page rendering tests', () => {
  pages.forEach(({ path, Component }) => {
    test(`renders ${path} without crashing`, () => {
      render(
        <Provider store={store}>
          <ThemeProvider>
            <QueryClientProviders>
              <BrowserRouter>
                <Component />
              </BrowserRouter>
            </QueryClientProviders>
          </ThemeProvider>
        </Provider>,
      );
    });
  });
});
