import { render, screen } from '@testing-library/react';
import { GlobalLoader } from '../Loader/GlobalLoader';

describe('GlobalLoader', () => {
  test('renders loading message when loading is true', () => {
    render(<GlobalLoader loading={true} message="Loading images..." />);

    expect(screen.getByText('Loading images...')).toBeInTheDocument();
  });

  test('renders empty container when loading is false', () => {
    const { container } = render(
      <GlobalLoader loading={false} message="Loading images..." />,
    );

    expect(screen.queryByText('Loading images...')).not.toBeInTheDocument();
    // renders an empty div
    expect(container.firstChild).toBeEmptyDOMElement();
  });

  const loadingMessages = [
    { message: 'Checking for updates...' },
    { message: 'Starting global face reclustering...' },
    { message: 'Adding folder...' },
  ];

  test.each(loadingMessages)(
    'displays "$message" correctly',
    ({ message }) => {
      render(<GlobalLoader loading={true} message={message} />);

      expect(screen.getByText(message)).toBeInTheDocument();
    },
  );
});
