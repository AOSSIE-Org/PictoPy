import { render } from '@testing-library/react';
import { AITagging } from '@/pages/AITagging/AITagging';
import Album from '../Album/Album';
import { Home } from '@/pages/Home/Home';
import Memories from '../Memories/Memories';
import Settings from '../SettingsPage/Settings';
import Videos from '../VideosPage/Videos';
import { ROUTES } from '@/constants/routes';
import QueryClientProviders from '@/config/QueryClientProvider';
import { MemoryRouter } from 'react-router';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { Provider } from 'react-redux';
import { store } from '@/app/store';
import { ReactNode } from 'react';

// Wrapper to fix React 19 type compatibility with react-router
const RouterWrapper = ({ children }: { children: ReactNode }) =>
  MemoryRouter({ children }) as React.JSX.Element;

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
