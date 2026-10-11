import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { MyFav } from '../Home/MyFav';
import { fetchAllImages, fetchAllVideos } from '@/api/api-functions';
import { Image, Video } from '@/types/Media';

jest.mock('@/api/api-functions', () => ({
  fetchAllImages: jest.fn(),
  fetchAllVideos: jest.fn(),
}));

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

jest.mock('@/hooks/useToggleFav', () => ({
  useToggleFav: () => ({
    toggleFavourite: jest.fn(),
    toggleFavouritePending: false,
  }),
}));

jest.mock('@/hooks/useToggleVideoFav', () => ({
  useToggleVideoFav: () => ({
    toggleFavourite: jest.fn(),
    toggleFavouritePending: false,
  }),
}));

const imageMetadata = {
  width: 100,
  height: 100,
  file_location: '/photos/summer-photo.jpg',
  file_size: 1,
  item_type: 'image/jpeg',
};

const videoMetadata = {
  width: 100,
  height: 100,
  file_location: '/videos/winter-clip.mp4',
  file_size: 1,
  item_type: 'video/mp4',
};

// The image's capture date is newer than the video's, but the video was
// favourited more recently than the image -- Date and Custom sort disagree
// on purpose, so tests can tell them apart.
const makeImage = (overrides: Partial<Image> = {}): Image => ({
  id: 'img-1',
  path: '/photos/summer-photo.jpg',
  thumbnailPath: '/photos/summer-photo-thumb.jpg',
  folder_id: 'folder-1',
  isTagged: false,
  isFavourite: true,
  favouritedAt: '2024-01-01 10:00:00',
  metadata: {
    ...imageMetadata,
    name: 'summer-photo.jpg',
    date_created: '2024-06-01T00:00:00',
  },
  ...overrides,
});

const makeVideo = (overrides: Partial<Video> = {}): Video => ({
  id: 'vid-1',
  path: '/videos/winter-clip.mp4',
  thumbnailPath: '/videos/winter-clip-thumb.jpg',
  folder_id: 'folder-1',
  isFavourite: true,
  favouritedAt: '2024-06-01 10:00:00',
  metadata: {
    ...videoMetadata,
    name: 'winter-clip.mp4',
    date_created: '2020-01-01T00:00:00',
  },
  ...overrides,
});

const openCustomSort = async (user: ReturnType<typeof userEvent.setup>) => {
  await user.click(screen.getByRole('button', { name: /Sort by/i }));
  await user.click(screen.getByRole('menuitem', { name: 'Custom' }));
};

describe('MyFav (Favorites) page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders favourited images and videos mixed together, excluding non-favourites', async () => {
    jest.mocked(fetchAllImages).mockResolvedValue({
      success: true,
      data: [
        makeImage(),
        makeImage({
          id: 'img-2',
          isFavourite: false,
          metadata: {
            ...imageMetadata,
            name: 'not-a-favourite.jpg',
            date_created: null,
          },
        }),
      ],
    });
    jest.mocked(fetchAllVideos).mockResolvedValue({
      success: true,
      data: [
        makeVideo(),
        makeVideo({
          id: 'vid-2',
          isFavourite: false,
          metadata: {
            ...videoMetadata,
            name: 'not-a-favourite.mp4',
            date_created: null,
          },
        }),
      ],
    });

    render(<MyFav />);

    expect(await screen.findByAltText('summer-photo.jpg')).toBeInTheDocument();
    expect(screen.getByLabelText('Play winter-clip.mp4')).toBeInTheDocument();
    expect(
      screen.queryByAltText('not-a-favourite.jpg'),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText('Play not-a-favourite.mp4'),
    ).not.toBeInTheDocument();
  });

  test('Date sort (default) groups items by month, newest capture date first', async () => {
    jest.mocked(fetchAllImages).mockResolvedValue({
      success: true,
      data: [makeImage()],
    });
    jest.mocked(fetchAllVideos).mockResolvedValue({
      success: true,
      data: [makeVideo()],
    });

    render(<MyFav />);
    await screen.findByAltText('summer-photo.jpg');

    const headers = screen
      .getAllByRole('heading', { level: 3 })
      .map((h) => h.textContent ?? '');
    const juneIndex = headers.findIndex((h) => h.includes('June 2024'));
    const januaryIndex = headers.findIndex((h) => h.includes('January 2020'));
    expect(juneIndex).toBeGreaterThanOrEqual(0);
    expect(januaryIndex).toBeGreaterThanOrEqual(0);
    expect(juneIndex).toBeLessThan(januaryIndex);
  });

  test('Custom sort orders by favourited time (most recent first) with no month grouping', async () => {
    jest.mocked(fetchAllImages).mockResolvedValue({
      success: true,
      data: [makeImage()],
    });
    jest.mocked(fetchAllVideos).mockResolvedValue({
      success: true,
      data: [makeVideo()],
    });

    const user = userEvent.setup();
    render(<MyFav />);
    await screen.findByAltText('summer-photo.jpg');

    await openCustomSort(user);

    // The video was favourited later than the image, even though the image
    // has the newer *capture* date -- Custom sort must follow favourited
    // time, not capture date.
    const videoEl = screen.getByLabelText('Play winter-clip.mp4');
    const imageEl = screen.getByAltText('summer-photo.jpg');
    expect(
      videoEl.compareDocumentPosition(imageEl) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.queryByText(/June 2024/)).not.toBeInTheDocument();
  });

  test('persists the selected sort option across a remount', async () => {
    jest.mocked(fetchAllImages).mockResolvedValue({
      success: true,
      data: [makeImage()],
    });
    jest.mocked(fetchAllVideos).mockResolvedValue({
      success: true,
      data: [makeVideo()],
    });

    const user = userEvent.setup();
    const { unmount } = render(<MyFav />);
    await screen.findByAltText('summer-photo.jpg');
    await openCustomSort(user);
    unmount();

    // A remount stands in for the reload that used to reset the sort.
    render(<MyFav />);
    await screen.findByAltText('summer-photo.jpg');
    expect(screen.queryByText(/June 2024/)).not.toBeInTheDocument();
  });

  test('excludes previously-loaded favourited videos while a face search is active', async () => {
    jest.mocked(fetchAllImages).mockResolvedValue({
      success: true,
      data: [],
    });
    jest.mocked(fetchAllVideos).mockResolvedValue({
      success: true,
      data: [],
    });

    render(<MyFav />, {
      preloadedState: {
        search: { active: true, queryImage: 'query.jpg' },
        images: {
          images: [makeImage({ id: 'search-hit' })],
          currentViewIndex: -1,
        },
        videos: { videos: [makeVideo()], currentViewIndex: -1 },
      },
    });

    expect(await screen.findByAltText('summer-photo.jpg')).toBeInTheDocument();
    expect(screen.getByText(/Face Search Results/)).toBeInTheDocument();
    expect(
      screen.queryByLabelText('Play winter-clip.mp4'),
    ).not.toBeInTheDocument();
  });
});
