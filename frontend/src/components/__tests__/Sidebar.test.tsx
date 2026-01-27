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
        <Route path="/" element={<div>Home Page</div>} />
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
    test('clicking Settings link navigates to /settings', async () => {
      const user = userEvent.setup();
      render(<SidebarWithRoutes />, { initialRoutes: ['/'] });

      expect(screen.getByTestId('location-display')).toHaveTextContent('/'); // start location

      await user.click(screen.getByText('Settings')); // click settings

      // verify
      expect(screen.getByTestId('location-display')).toHaveTextContent(
        '/settings',
      );
      expect(screen.getByText('Settings Page')).toBeInTheDocument();
    });

    test('clicking Home link navigates to /home', async () => {
      const user = userEvent.setup();
      render(<SidebarWithRoutes />, { initialRoutes: ['/settings'] });

      // start location
      expect(screen.getByTestId('location-display')).toHaveTextContent(
        '/settings',
      );

      await user.click(screen.getByText('Home')); // click home

      // verify
      expect(screen.getByTestId('location-display')).toHaveTextContent('/home');
      expect(screen.getByText('Home Page')).toBeInTheDocument();
    });

    test('clicking AI Tagging link navigates to /ai-tagging', async () => {
      const user = userEvent.setup();
      render(<SidebarWithRoutes />, { initialRoutes: ['/'] });

      await user.click(screen.getByText('AI Tagging')); // click ai-tagging

      // verify
      expect(screen.getByTestId('location-display')).toHaveTextContent(
        '/ai-tagging',
      );
      expect(screen.getByText('AI Tagging Page')).toBeInTheDocument();
    });

    test('clicking Favourites link navigates to /favourites', async () => {
      const user = userEvent.setup();
      render(<SidebarWithRoutes />, { initialRoutes: ['/'] });

      await user.click(screen.getByText('Favourites')); // click favourites

      // verify
      expect(screen.getByTestId('location-display')).toHaveTextContent(
        '/favourites',
      );
      expect(screen.getByText('Favourites Page')).toBeInTheDocument();
    });

    test('clicking Videos link navigates to /videos', async () => {
      const user = userEvent.setup();
      render(<SidebarWithRoutes />, { initialRoutes: ['/'] });

      await user.click(screen.getByText('Videos')); // click videos

      // verify
      expect(screen.getByTestId('location-display')).toHaveTextContent(
        '/videos',
      );
      expect(screen.getByText('Videos Page')).toBeInTheDocument();
    });

    test('clicking Albums link navigates to /albums', async () => {
      const user = userEvent.setup();
      render(<SidebarWithRoutes />, { initialRoutes: ['/'] });

      await user.click(screen.getByText('Albums')); // click albums

      // verify
      expect(screen.getByTestId('location-display')).toHaveTextContent(
        '/albums',
      );
      expect(screen.getByText('Albums Page')).toBeInTheDocument();
    });

    test('clicking Memories link navigates to /memories', async () => {
      const user = userEvent.setup();
      render(<SidebarWithRoutes />, { initialRoutes: ['/'] });

      await user.click(screen.getByText('Memories')); // click memories

      // verify
      expect(screen.getByTestId('location-display')).toHaveTextContent(
        '/memories',
      );
      expect(screen.getByText('Memories Page')).toBeInTheDocument();
    });
  });
});
