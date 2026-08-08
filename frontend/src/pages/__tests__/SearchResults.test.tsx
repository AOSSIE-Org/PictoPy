import { render, screen, waitFor, fireEvent } from '@/test-utils';
import { useNavigate } from 'react-router';
import { SearchResults } from '../SearchResults/SearchResults';
import {
  searchImagesByTag,
  searchVideosByTag,
  fetchAllClusters,
  fetchMultiPersonSearch,
} from '@/api/api-functions';

// Mock the API functions. fetchModelStatus must resolve to a well-formed
// response even in tests that don't care about it -- the "no tag matches"
// auto-mode path calls it to decide whether to fall back to semantic search.
jest.mock('@/api/api-functions', () => ({
  searchImagesByTag: jest.fn(),
  semanticSearchImages: jest.fn(),
  searchVideosByTag: jest.fn(),
  semanticSearchVideos: jest.fn(),
  fetchModelStatus: jest.fn().mockResolvedValue({ success: true, data: {} }),
  fetchAllClusters: jest.fn(),
  fetchMultiPersonSearch: jest.fn(),
}));

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

const CLUSTERS = [
  { cluster_id: 'c1', cluster_name: 'Person A', face_count: 5 },
  { cluster_id: 'c2', cluster_name: 'Person B', face_count: 4 },
];

describe('SearchResults Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Videos default to no matches; the tests that care override this.
    (searchVideosByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
    });
    // Every query waits on the cluster list to decide if it names people.
    (fetchAllClusters as jest.Mock).mockResolvedValue({
      success: true,
      data: { clusters: CLUSTERS },
    });
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

    // Neither search runs when there's no query
    expect(searchImagesByTag).not.toHaveBeenCalled();
    expect(searchVideosByTag).not.toHaveBeenCalled();

    // Check for empty state message
    expect(
      screen.getByText(/Please enter a search term to find/i),
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

    // API should be called once the cluster list has ruled out a people query
    await waitFor(() =>
      expect(searchImagesByTag).toHaveBeenCalledWith({ tag: 'cat' }),
    );

    // Header should reflect the query
    expect(screen.getByText('Results for "cat"')).toBeInTheDocument();

    // Wait for images to render
    await waitFor(() => {
      expect(
        screen.queryByText(/No photos or videos found matching your search/i),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText(/Please enter a search term/i),
      ).not.toBeInTheDocument();
    });
  });

  test('renders matching videos in their own section', async () => {
    (searchImagesByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
    });
    (searchVideosByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [
        {
          id: 'v1',
          path: '/clip.mp4',
          thumbnailPath: '/clip-thumb.jpg',
          folder_id: '1',
          tags: ['beach'],
          metadata: { name: 'clip.mp4' },
        },
      ],
    });

    renderWithQuery('beach');

    await waitFor(() =>
      expect(searchVideosByTag).toHaveBeenCalledWith({ tag: 'beach' }),
    );

    await waitFor(() => {
      expect(screen.getByText('Videos')).toBeInTheDocument();
      expect(screen.getByLabelText(/Play clip.mp4/i)).toBeInTheDocument();
    });
  });

  test('renders no results state when both APIs return empty arrays', async () => {
    (searchImagesByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithQuery('unicorn');

    await waitFor(() => {
      expect(
        screen.getByText(/No photos or videos found matching your search/i),
      ).toBeInTheDocument();
    });
  });

  test('a photo-search error is shown inline and does not hide video results', async () => {
    (searchImagesByTag as jest.Mock).mockRejectedValue(
      new Error('Network Error'),
    );
    (searchVideosByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [
        {
          id: 'v1',
          path: '/clip.mp4',
          thumbnailPath: '/clip-thumb.jpg',
          folder_id: '1',
          tags: ['beach'],
          metadata: { name: 'clip.mp4' },
        },
      ],
    });

    renderWithQuery('dog');

    await waitFor(
      () => {
        // Inline photo error, not the full-screen takeover...
        expect(
          screen.getByText(/Couldn't load photo results/i),
        ).toBeInTheDocument();
        expect(screen.queryByText(/^Search Failed$/i)).not.toBeInTheDocument();
        // ...and the videos still render.
        expect(screen.getByText('Videos')).toBeInTheDocument();
        expect(screen.getByLabelText(/Play clip.mp4/i)).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  test('a video-search error is shown inline and does not hide photo results', async () => {
    (searchImagesByTag as jest.Mock).mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          path: '/img1.jpg',
          thumbnailPath: '/thumb1.jpg',
          tags: ['cat'],
        },
      ],
    });
    (searchVideosByTag as jest.Mock).mockRejectedValue(
      new Error('Network Error'),
    );

    renderWithQuery('cat');

    await waitFor(
      () => {
        // Inline video error, not the full-screen takeover...
        expect(
          screen.getByText(/Couldn't load video results/i),
        ).toBeInTheDocument();
        expect(screen.queryByText(/^Search Failed$/i)).not.toBeInTheDocument();
        // ...and the photos still render.
        expect(
          screen.queryByText(/Couldn't load photo results/i),
        ).not.toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  describe('text-based multi-person search', () => {
    test('a two-name query runs a match_all people search instead of tag search', async () => {
      (fetchMultiPersonSearch as jest.Mock).mockResolvedValue({
        success: true,
        data: {
          images: [
            {
              id: 'p1',
              path: '/together.jpg',
              thumbnailPath: '/together-thumb.jpg',
              metadata: { name: 'together.jpg' },
              match_count: 2,
            },
          ],
          total: 1,
          match_mode: 'match_all',
        },
      });

      renderWithQuery('Person A and Person B');

      await waitFor(() =>
        expect(fetchMultiPersonSearch).toHaveBeenCalledWith({
          cluster_ids: ['c1', 'c2'],
          match_mode: 'match_all',
        }),
      );

      expect(
        await screen.findByText('Photos with all of:'),
      ).toBeInTheDocument();
      // The people path replaces tag/semantic search rather than joining it.
      expect(searchImagesByTag).not.toHaveBeenCalled();
      expect(searchVideosByTag).not.toHaveBeenCalled();
    });

    test('"or" between names searches for any of them', async () => {
      (fetchMultiPersonSearch as jest.Mock).mockResolvedValue({
        success: true,
        data: { images: [], total: 0, match_mode: 'match_any' },
      });

      renderWithQuery('Person A or Person B');

      await waitFor(() =>
        expect(fetchMultiPersonSearch).toHaveBeenCalledWith({
          cluster_ids: ['c1', 'c2'],
          match_mode: 'match_any',
        }),
      );

      expect(
        await screen.findByText('Photos with any of:'),
      ).toBeInTheDocument();
      expect(
        await screen.findByText(/No photos found with these people in them/i),
      ).toBeInTheDocument();
    });

    test('an unknown name is called out and the known people are still searched', async () => {
      (fetchMultiPersonSearch as jest.Mock).mockResolvedValue({
        success: true,
        data: { images: [], total: 0, match_mode: 'match_all' },
      });

      renderWithQuery('Person A, Zed, Person B');

      await waitFor(() =>
        expect(fetchMultiPersonSearch).toHaveBeenCalledWith({
          cluster_ids: ['c1', 'c2'],
          match_mode: 'match_all',
        }),
      );

      expect(
        await screen.findByText(/No one is named Zed/i),
      ).toBeInTheDocument();
    });

    test('a query naming only one known person falls through to tag search', async () => {
      (searchImagesByTag as jest.Mock).mockResolvedValue({
        success: true,
        data: [],
      });

      renderWithQuery('Person A and Zed');

      await waitFor(() =>
        expect(searchImagesByTag).toHaveBeenCalledWith({
          tag: 'Person A and Zed',
        }),
      );
      expect(fetchMultiPersonSearch).not.toHaveBeenCalled();
    });

    test('mode=tag opts out of people search without fetching clusters', async () => {
      (searchImagesByTag as jest.Mock).mockResolvedValue({
        success: true,
        data: [],
      });

      render(<SearchResults />, {
        initialRoutes: ['/search?value=Person%20A%20and%20Person%20B&mode=tag'],
      });

      // An explicit mode never consults the clusters, so it must not wait on
      // (or pay for) the fetch.
      expect(fetchAllClusters).not.toHaveBeenCalled();

      await waitFor(() =>
        expect(searchImagesByTag).toHaveBeenCalledWith({
          tag: 'Person A and Person B',
        }),
      );
      expect(fetchMultiPersonSearch).not.toHaveBeenCalled();
    });

    test('a failed people search shows the Search Failed takeover', async () => {
      (fetchMultiPersonSearch as jest.Mock).mockRejectedValue(
        new Error('Network Error'),
      );

      renderWithQuery('Person A and Person B');

      await waitFor(
        () => {
          expect(screen.getByText(/Search Failed/i)).toBeInTheDocument();
          expect(screen.getByText(/Network Error/i)).toBeInTheDocument();
        },
        { timeout: 5000 },
      );
    });
  });

  test('the Search Failed takeover appears only when both searches fail', async () => {
    (searchImagesByTag as jest.Mock).mockRejectedValue(
      new Error('Network Error'),
    );
    (searchVideosByTag as jest.Mock).mockRejectedValue(
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

  test('resets the main scroll container to the top on a new search', async () => {
    // The real scroll container lives in the layout, which this page-level
    // test does not mount. Stand one in and give its scrollTo the same
    // observable effect a browser has -- it updates scrollTop -- so the test
    // can assert the user-visible scroll state rather than a spy call.
    const scrollContainer = document.createElement('div');
    scrollContainer.id = 'main-scroll-container';
    const scrollTo = jest.fn((options?: ScrollToOptions) => {
      if (typeof options?.top === 'number') {
        scrollContainer.scrollTop = options.top;
      }
    });
    // Define the property directly instead of casting a jest.fn onto the
    // read-only overloaded HTMLElement['scrollTo'] signature.
    Object.defineProperty(scrollContainer, 'scrollTo', {
      value: scrollTo,
      writable: true,
      configurable: true,
    });
    document.body.appendChild(scrollContainer);

    // Navigate within the same mounted SearchResults so the transition mirrors
    // a real new search (query param changes, component stays mounted) rather
    // than a fresh mount whose effect would trivially fire once.
    const GoToSearch = ({ to }: { to: string }) => {
      const navigate = useNavigate();
      return (
        <button type="button" onClick={() => navigate(to)}>
          go to {to}
        </button>
      );
    };

    try {
      (searchImagesByTag as jest.Mock).mockResolvedValue({
        success: true,
        data: [
          {
            id: '1',
            path: '/img1.jpg',
            thumbnailPath: '/thumb1.jpg',
            tags: ['cat'],
          },
        ],
      });

      render(
        <>
          <GoToSearch to="/search?value=motorcycle" />
          <SearchResults />
        </>,
        { initialRoutes: ['/search?value=cat'] },
      );

      // Let the initial search settle so we isolate the new-search transition.
      await waitFor(() => {
        expect(screen.getByText('Results for "cat"')).toBeInTheDocument();
      });

      // Simulate the user having scrolled the previous, longer result set to
      // the bottom, then start observing from a clean slate.
      scrollContainer.scrollTop = 500;
      scrollTo.mockClear();

      // Run the new search on the still-mounted component.
      fireEvent.click(screen.getByRole('button', { name: /motorcycle/i }));

      await waitFor(() => {
        expect(
          screen.getByText('Results for "motorcycle"'),
        ).toBeInTheDocument();
        // The user-visible result: the viewport is back at the top.
        expect(scrollContainer.scrollTop).toBe(0);
      });
      expect(scrollTo).toHaveBeenCalledWith({ top: 0 });
    } finally {
      document.body.removeChild(scrollContainer);
    }
  });
});
