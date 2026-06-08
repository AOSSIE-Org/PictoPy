import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Routes, Route, useLocation } from 'react-router';
import { AppSidebar } from '../Navigation/Sidebar/AppSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { ROUTES } from '@/constants/routes';

// Display current routes
const LocationDisplay = () => {
  const location = useLocation();
  return <div data-testid="location-display">{location.pathname}</div>;
};

// Sidebar + routes display
const SidebarWithRoutes = () => (
  <SidebarProvider>
    <AppSidebar />
    <main>
      <LocationDisplay />
      <Routes>
        <Route path={ROUTES.HOME} element={<div>Home Page</div>} />
        <Route path={ROUTES.SETTINGS} element={<div>Settings Page</div>} />
        <Route path={ROUTES.AI} element={<div>AI Tagging Page</div>} />
        <Route path={ROUTES.FAVOURITES} element={<div>Favourites Page</div>} />
        <Route path={ROUTES.VIDEOS} element={<div>Videos Page</div>} />
        <Route path={ROUTES.ALBUMS} element={<div>Albums Page</div>} />
        <Route path={ROUTES.MEMORIES} element={<div>Memories Page</div>} />
      </Routes>
    </main>
  </SidebarProvider>
);

describe('Sidebar', () => {
  describe('Structure Tests', () => {
    test('renders all main navigation links', () => {
      render(
        <SidebarProvider>
          <AppSidebar />
        </SidebarProvider>,
      );

      // Verify key navigation items exist
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('AI Tagging')).toBeInTheDocument();
      expect(screen.getByText('Favourites')).toBeInTheDocument();
      expect(screen.getByText('Videos')).toBeInTheDocument();
      expect(screen.getByText('Albums')).toBeInTheDocument();
      expect(screen.getByText('Memories')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });

  describe('Navigation Interaction Tests', () => {
    const navigationCases = [
      {
        linkText: 'Home',
        route: ROUTES.HOME,
        pageText: 'Home Page',
        startRoute: ROUTES.SETTINGS,
      },
      { linkText: 'AI Tagging', route: ROUTES.AI, pageText: 'AI Tagging Page' },
      {
        linkText: 'Favourites',
        route: ROUTES.FAVOURITES,
        pageText: 'Favourites Page',
      },
      { linkText: 'Videos', route: ROUTES.VIDEOS, pageText: 'Videos Page' },
      { linkText: 'Albums', route: ROUTES.ALBUMS, pageText: 'Albums Page' },
      {
        linkText: 'Memories',
        route: ROUTES.MEMORIES,
        pageText: 'Memories Page',
      },
      {
        linkText: 'Settings',
        route: ROUTES.SETTINGS,
        pageText: 'Settings Page',
      },
    ];

    test.each(navigationCases)(
      'clicking $linkText link navigates to /$route',
      async ({ linkText, route, pageText, startRoute = ROUTES.HOME }) => {
        const user = userEvent.setup();
        render(<SidebarWithRoutes />, { initialRoutes: [`/${startRoute}`] });

        // verify start location
        expect(screen.getByTestId('location-display')).toHaveTextContent(
          `/${startRoute}`,
        );

        // click nav link
        await user.click(screen.getByText(linkText));

        // verify navigation
        expect(screen.getByTestId('location-display')).toHaveTextContent(
          `/${route}`,
        );
        expect(screen.getByText(pageText)).toBeInTheDocument();
      },
    );
  });
});
