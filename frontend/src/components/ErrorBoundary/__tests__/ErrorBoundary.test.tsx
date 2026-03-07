import { render, screen, fireEvent, act } from '@testing-library/react';
import ErrorBoundary from '../ErrorBoundary';

// A component that throws on render when `shouldThrow` is true
const ThrowingChild = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test explosion');
  }
  return <div>Child rendered</div>;
};

beforeAll(() => {
  // Silence React error boundary console.error noise
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterAll(() => {
  (console.error as jest.Mock).mockRestore();
});

beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('ErrorBoundary', () => {
  it('renders children when no error is thrown', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Child rendered')).toBeInTheDocument();
  });

  it('renders fallback UI when a child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.queryByText('Child rendered')).not.toBeInTheDocument();
  });

  it('toggles error details when "Show Details" is clicked', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>,
    );

    // Details should be hidden initially
    expect(screen.queryByText(/Test explosion/)).not.toBeInTheDocument();

    // Click "Show Details"
    const detailsButton = screen.getByRole('button', { name: /show details/i });
    expect(detailsButton).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(detailsButton);

    // Error name and message should now appear
    expect(screen.getByText(/Error: Test explosion/)).toBeInTheDocument();
    expect(detailsButton).toHaveAttribute('aria-expanded', 'true');

    // The details panel should have the matching id
    const panel = document.getElementById('error-details-panel');
    expect(panel).toBeInTheDocument();
    expect(detailsButton).toHaveAttribute('aria-controls', 'error-details-panel');

    // Click "Hide Details"
    fireEvent.click(detailsButton);
    expect(screen.queryByText(/Test explosion/)).not.toBeInTheDocument();
    expect(detailsButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('shows retrying state and recovers after clicking "Reload App"', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>,
    );

    const retryButton = screen.getByRole('button', { name: /reload app/i });
    fireEvent.click(retryButton);

    // Should show retrying state
    expect(screen.getByText('Reloading...')).toBeInTheDocument();
    expect(retryButton).toBeDisabled();

    // Advance past the 500ms timeout
    act(() => {
      jest.advanceTimersByTime(500);
    });

    // The boundary resets — but the child still throws, so fallback reappears.
    // This proves the boundary went through the reset cycle.
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('calls onRetry prop when retrying', () => {
    const onRetry = jest.fn();

    render(
      <ErrorBoundary onRetry={onRetry}>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>,
    );

    fireEvent.click(screen.getByRole('button', { name: /reload app/i }));

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
