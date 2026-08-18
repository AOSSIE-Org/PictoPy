import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import { GlobalLoader } from '@/components/Loader/GlobalLoader';
import AlbumDetail from '../Album/AlbumDetail';

import {
  getAlbumById,
  getAlbumImages,
  fetchAllImages,
} from '@/api/api-functions';

// Mock Tauri convertFileSrc API
jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
  convertFileSrc: (path: string) => `tauri-converted://${path}`,
}));

jest.mock('@/api/api-functions', () => ({
  getAlbumById: jest.fn(),
  getAlbumImages: jest.fn(),
  fetchAllImages: jest.fn(),
  removeMultipleImagesFromAlbum: jest.fn(),
  addImagesToAlbum: jest.fn(),
}));

const mockGetAlbumById = getAlbumById as jest.Mock;
const mockGetAlbumImages = getAlbumImages as jest.Mock;
const mockFetchAllImages = fetchAllImages as jest.Mock;

const AlbumDetailWithLoader = () => {
  const { loading, message } = useSelector((state: RootState) => state.loader);
  return (
    <>
      <Routes>
        <Route path="/albums/:albumId" element={<AlbumDetail />} />
        <Route path="/albums" element={<div>Albums list</div>} />
      </Routes>
      <GlobalLoader loading={loading} message={message} />
    </>
  );
};

const renderDetail = () =>
  render(<AlbumDetailWithLoader />, { initialRoutes: ['/albums/a1'] });

describe('AlbumDetail', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetAlbumById.mockResolvedValue({
      success: true,
      data: {
        album: {
          album_id: 'a1',
          album_name: 'Trip',
          description: '',
          is_locked: false,
          cover_image_path: null,
          image_count: 1,
        },
      },
    });
    mockGetAlbumImages.mockResolvedValue({ success: true, image_ids: ['i1'] });
    mockFetchAllImages.mockResolvedValue({
      success: true,
      data: [{ id: 'i1', path: '/p/i1.jpg', thumbnailPath: '/p/i1.jpg' }],
    });
  });

  test('shows skeletons while images load instead of a blocking loader', async () => {
    let releaseImages: (value: unknown) => void = () => {};
    mockGetAlbumImages.mockImplementation(
      () =>
        new Promise((resolve) => {
          releaseImages = resolve;
        }),
    );

    const { store } = renderDetail();

    await screen.findByText('Trip');
    expect(
      await screen.findAllByTestId('album-image-skeleton'),
    ).not.toHaveLength(0);
    // The empty state must not claim the album is empty mid-load.
    expect(
      screen.queryByText(/no images in this album/i),
    ).not.toBeInTheDocument();
    expect(store.getState().loader.loading).toBe(false);

    releaseImages({ success: true, image_ids: ['i1'] });

    await waitFor(() =>
      expect(screen.queryAllByTestId('album-image-skeleton')).toHaveLength(0),
    );
  }, 30000);

  // Leaving while a request was in flight used to leave showLoader dispatched
  // with nothing to clear it, freezing the app behind the overlay.
  test('does not strand the global loader when leaving mid-load', async () => {
    mockGetAlbumImages.mockImplementation(() => new Promise(() => {}));

    const { store, unmount } = renderDetail();

    await screen.findByText('Trip');
    await waitFor(() => expect(mockGetAlbumImages).toHaveBeenCalled());

    unmount();

    expect(store.getState().loader.loading).toBe(false);
  }, 30000);

  // The cover is whatever image comes first in the album, so there is nothing
  // to pick and no per-image menu left to pick it from.
  test('offers no per-image cover menu', async () => {
    const user = userEvent.setup();
    renderDetail();

    const tile = await screen.findByAltText('i1.jpg');
    await user.pointer({ keys: '[MouseRight]', target: tile });

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(screen.queryByText(/set as cover/i)).not.toBeInTheDocument();
  }, 30000);

  test('places the album header controls before the album title', async () => {
    mockGetAlbumById.mockResolvedValue({
      success: true,
      data: {
        album: {
          album_id: 'a1',
          album_name: 'Trip',
          description: 'Summer archive',
          is_locked: false,
          cover_image_path: null,
          image_count: 1,
        },
      },
    });

    renderDetail();

    const backButton = await screen.findByRole('button', {
      name: /back to albums/i,
    });
    const albumTitle = await screen.findByRole('heading', { name: 'Trip' });

    expect(
      backButton.compareDocumentPosition(albumTitle) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByText('Summer archive')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /select images/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /add images/i }),
    ).toBeInTheDocument();
    expect(screen.getByText('1 photo')).toBeInTheDocument();
  }, 30000);
});
