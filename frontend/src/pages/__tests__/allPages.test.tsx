import { store } from '@/app/store';
import QueryClientProviders from '@/config/QueryClientProvider';
import { ROUTES } from '@/constants/routes';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AITagging } from '@/pages/AITagging/AITagging';
import { Home } from '@/pages/Home/Home';
import { render } from '@testing-library/react';
import { ReactNode } from 'react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router';
import Album from '../Album/Album';
import Memories from '../Memories/Memories';
import Settings from '../SettingsPage/Settings';
import Videos from '../VideosPage/Videos';

// Wrapper component using proper JSX syntax for React 19 + react-router compatibility
const RouterWrapper = ({ children }: { children: ReactNode }) => {
  return <MemoryRouter>{children}</MemoryRouter>;
};

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
  { path: ROUTES.HOME, Component: Home },
  { path: ROUTES.VIDEOS, Component: Videos },
  { path: ROUTES.SETTINGS, Component: Settings },
  { path: ROUTES.AI, Component: AITagging },
  { path: ROUTES.ALBUMS, Component: Album },
  { path: ROUTES.MEMORIES, Component: Memories },
];

describe('Page rendering tests', () => {
  pages.forEach(({ path, Component }) => {
    test(`renders ${path} without crashing`, () => {
      render(
        <Provider store={store}>
          <ThemeProvider>
            <QueryClientProviders>
              <RouterWrapper>
                <Component />
              </RouterWrapper>
            </QueryClientProviders>
          </ThemeProvider>
        </Provider>,
      );
    });
  });
});
