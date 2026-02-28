import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { InfoDialog } from '../Dialog/InfoDialog';

describe('InfoDialog', () => {
  const defaultProps = {
    isOpen: true,
    title: 'Test Title',
    message: 'Test message content',
    variant: 'info' as const,
    showCloseButton: true,
  };

  describe('Rendering', () => {
    test('renders title and message when open', () => {
      render(<InfoDialog {...defaultProps} />);

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test message content')).toBeInTheDocument();
    });

    test('does not render content when closed', () => {
      render(<InfoDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Test Title')).not.toBeInTheDocument();
    });

    const variantCases = [
      { variant: 'info' as const, label: 'info' },
      { variant: 'error' as const, label: 'error' },
    ];

    test.each(variantCases)(
      'renders with $label variant without crashing',
      ({ variant }) => {
        render(
          <InfoDialog {...defaultProps} variant={variant} />,
        );

        expect(screen.getByText('Test Title')).toBeInTheDocument();
        expect(screen.getByText('Test message content')).toBeInTheDocument();
      },
    );
  });

  describe('Interactions', () => {
    test('close button is rendered when showCloseButton is true', () => {
      render(<InfoDialog {...defaultProps} />);

      const closeButtons = screen.getAllByRole('button', { name: /close/i });
      // action button + dialog X button
      expect(closeButtons.length).toBeGreaterThanOrEqual(1);
    });

    test('clicking close button dispatches hideInfoDialog', async () => {
      const user = userEvent.setup();
      const { store } = render(<InfoDialog {...defaultProps} />);

      // Target the explicit "Close" action button (data-slot="button"),
      // not the dialog's built-in X close button (data-slot="dialog-close")
      const actionButton = screen
        .getAllByRole('button', { name: /close/i })
        .find((btn) => btn.getAttribute('data-slot') === 'button')!;
      await user.click(actionButton);

      // verify store updated - dialog should be closed
      const state = (store.getState() as any).infoDialog;
      expect(state.isOpen).toBe(false);
    });
  });
});
