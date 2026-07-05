import { render, screen, waitFor } from '@/test-utils';
import { SearchResults } from '../SearchResults/SearchResults';
import { searchImagesByTag } from '@/api/api-functions';

// Mock the API function
jest.mock('@/api/api-functions', () => ({
  searchImagesByTag: jest.fn(),
}));

describe('SearchResults Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithQuery = (queryValue: string) => {
    // MemoryRouter in test-utils defaults to initialEntries=['/']
    // We can pass initialRoutes via options to inject search params
    return render(<SearchResults />, {
      initialRoutes: [`/search?value=${encodeURIComponent(queryValue)}`],
    });
  };

  test('renders empty state when no query is provided', async () => {
    renderWithQuery('');

    // Should not call the API if query is empty
    expect(searchImagesByTag).not.toHaveBeenCalled();

    // Check for empty state message
    expect(
      screen.getByText(/Please enter a search term to find images/i),
    ).toBeInTheDocument();
  });

  test('renders loading and success state with images', async () => {
    // Mock successful API response
    (searchImagesByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          path: '/img1.jpg',
          thumbnailPath: '/thumb1.jpg',
          tags: ['cat'],
        },
        {
          id: '2',
          path: '/img2.jpg',
          thumbnailPath: '/thumb2.jpg',
          tags: ['cat'],
        },
      ],
    });

    renderWithQuery('cat');

    // API should be called
    expect(searchImagesByTag).toHaveBeenCalledWith({ tag: 'cat' });

    // Header should reflect the query
    expect(screen.getByText('Results for "cat"')).toBeInTheDocument();

    // Wait for images to render
    await waitFor(() => {
      expect(
        screen.queryByText(/No images found matching your search/i),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText(/Please enter a search term/i),
      ).not.toBeInTheDocument();
    });
  });

  test('renders no images found state when API returns empty array', async () => {
    (searchImagesByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithQuery('unicorn');

    await waitFor(() => {
      expect(
        screen.getByText(/No images found matching your search/i),
      ).toBeInTheDocument();
    });
  });

  test('renders error state when API request fails', async () => {
    (searchImagesByTag as jest.Mock).mockRejectedValue(
      new Error('Network Error'),
    );

    renderWithQuery('dog');

    await waitFor(
      () => {
        expect(screen.getByText(/Search Failed/i)).toBeInTheDocument();
        expect(screen.getByText(/Network Error/i)).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });
});
