import { render, screen, waitFor } from '@/test-utils';
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
      await screen.findByText('Light');
      expect(screen.getByText('Dark')).toBeInTheDocument();
      expect(screen.getByText('System')).toBeInTheDocument();
    });

    const themeSelectionCases = [
      { theme: 'Light', expectedClass: 'light', hiddenOption: 'Dark' },
      { theme: 'Dark', expectedClass: 'dark', hiddenOption: 'Light' },
      { theme: 'System', expectedClass: 'light', hiddenOption: 'Dark' }, // system resolves to light (matchMedia mock returns false)
    ];

    test.each(themeSelectionCases)(
      'selecting $theme theme applies class and closes dropdown',
      async ({ theme, expectedClass, hiddenOption }) => {
        const user = userEvent.setup();
        render(<ThemeSelector />);

        const button = screen.getByRole('button', { name: /themes/i });
        await user.click(button); // open dropdown

        const themeOption = screen.getByText(theme);
        await user.click(themeOption); // select theme

        // verify theme class is applied to document
        await waitFor(() =>
          expect(document.documentElement).toHaveClass(expectedClass),
        );

        // verify dropdown closed
        await waitFor(() =>
          expect(screen.queryByText(hiddenOption)).not.toBeInTheDocument(),
        );
      },
    );
  });
});
