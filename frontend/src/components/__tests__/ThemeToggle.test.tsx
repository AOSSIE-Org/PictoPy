import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { ThemeSelector } from '../ThemeToggle';

describe('ThemeSelector', () => {
  describe('Structure Tests', () => {
    test('renders theme toggle button', () => {
      render(<ThemeSelector />);

      // button should be accessible
      const button = screen.getByRole('button', { name: /themes/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Interaction Tests', () => {
    test('clicking toggle button opens theme dropdown', async () => {
      const user = userEvent.setup();
      render(<ThemeSelector />);

      const button = screen.getByRole('button', { name: /themes/i });
      await user.click(button); // open dropdown

      // verify dropdown options are visible
      expect(screen.getByText('Light')).toBeInTheDocument();
      expect(screen.getByText('Dark')).toBeInTheDocument();
      expect(screen.getByText('System')).toBeInTheDocument();
    });

    test('selecting Dark theme option closes dropdown', async () => {
      const user = userEvent.setup();
      render(<ThemeSelector />);

      const button = screen.getByRole('button', { name: /themes/i });
      await user.click(button); // open dropdown

      const darkOption = screen.getByText('Dark');
      await user.click(darkOption); // select dark

      // dropdown should close (options no longer visible)
      expect(screen.queryByText('Light')).not.toBeInTheDocument();
    });

    test('selecting Light theme option closes dropdown', async () => {
      const user = userEvent.setup();
      render(<ThemeSelector />);

      const button = screen.getByRole('button', { name: /themes/i });
      await user.click(button); // open dropdown

      const lightOption = screen.getByText('Light');
      await user.click(lightOption); // select light

      // dropdown should close
      expect(screen.queryByText('Dark')).not.toBeInTheDocument();
    });
  });
});
