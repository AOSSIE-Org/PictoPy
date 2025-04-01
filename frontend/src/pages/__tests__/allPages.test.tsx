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
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { fetchImagesForHome } from '@/loader/fetchImages';
import { fetchAllImageObjects } from '@/loader/fetchAIImages';
import { fetchAlbums } from '@/loader/fetchAlbums';

const pages = [
  {
    path: ROUTES.LAYOUT.HOME,
    Component: Dashboard,
    loader: fetchImagesForHome,
  },
  { path: ROUTES.LAYOUT.VIDEOS, Component: Videos },
  { path: ROUTES.LAYOUT.SETTINGS, Component: Settings },
  {
    path: ROUTES.LAYOUT.AI,
    Component: AITagging,
    loader: fetchAllImageObjects,
  },
  { path: ROUTES.LAYOUT.ALBUM, Component: Album, loader: fetchAlbums },
  { path: ROUTES.LAYOUT.SECURE_FOLDER, Component: SecureFolder },
  { path: ROUTES.LAYOUT.MEMORIES, Component: Memories },
  { path: ROUTES.INITIAL, Component: InitialPage },
];

describe('Page rendering tests', () => {
  pages.forEach(({ path, Component, loader }) => {
    test(`renders ${path} without crashing`, async () => {
      let router;
      let mockLoader;

      if (loader || path === ROUTES.INITIAL) {
        // Add condition for InitialPage
        if (loader) {
          // Mock the loader to return undefined
          mockLoader = jest.fn().mockResolvedValue(undefined);
        }

        router = createMemoryRouter([
          {
            path: path,
            element: <Component />,
            ...(loader && { loader: mockLoader }), // Conditionally add loader
          },
        ]);
      }

      render(
        <ThemeProvider>
          <QueryClientProviders>
            {router ? <RouterProvider router={router} /> : <Component />}
          </QueryClientProviders>
        </ThemeProvider>,
      );
    });
  });
});
