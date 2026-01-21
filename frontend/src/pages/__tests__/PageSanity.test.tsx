import { render, screen } from '@/test-utils';
import { Home } from '../Home/Home';
import Settings from '../SettingsPage/Settings';

describe('Page Sanity Tests', () => {
  describe('Home Page', () => {
    test('renders home page structure', async () => {
      render(<Home />);
      expect(
        await screen.findByText(
          /Image Gallery|No Images to Display|Loading images/i,
        ),
      ).toBeInTheDocument();
    });
  });

  describe('Settings Page', () => {
    test('renders settings page sections', () => {
      render(<Settings />);

      expect(screen.getByText('Folder Management')).toBeInTheDocument();
      expect(screen.getByText('User Preferences')).toBeInTheDocument();
      expect(screen.getByText('Application Controls')).toBeInTheDocument();

      expect(
        screen.getByRole('button', { name: /Check for Updates/i }),
      ).toBeInTheDocument();
      expect(screen.getByText('GPU Acceleration')).toBeInTheDocument();
    });
  });
});
