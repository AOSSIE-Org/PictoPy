import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Route, Routes, useNavigate } from 'react-router';
import { useSelector } from 'react-redux';
import { onlineManager } from '@tanstack/react-query';
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

// Stands in for the albums page, reopening the album the way its unlock
// dialog does.
const AlbumsListStub = () => {
  const navigate = useNavigate();
  return (
    <div>
      Albums list
      <button
        onClick={() =>
          navigate('/albums/a1', { state: { password: 'old-password' } })
        }
      >
        Reopen
      </button>
    </div>
  );
};

const AlbumDetailWithLoader = () => {
  const { loading, message } = useSelector((state: RootState) => state.loader);
  return (
    <>
      <Routes>
        <Route path="/albums/:albumId" element={<AlbumDetail />} />
        <Route path="/albums" element={<AlbumsListStub />} />
      </Routes>
      <GlobalLoader loading={loading} message={message} />
    </>
  );
};

// Records whether `text` was ever inserted into the page. Reads the mutation
// records rather than the current DOM, since a node can be added and removed
// before the observer callback runs.
const watchForInsertedText = (text: string) => {
  let seen = false;
  const observer = new MutationObserver((records) => {
    for (const record of records) {
      const nodes =
        record.type === 'characterData'
          ? [record.target]
          : Array.from(record.addedNodes);
      if (nodes.some((node) => node.textContent?.includes(text))) seen = true;
    }
  });
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  return {
    stop: () => {
      observer.disconnect();
      return seen;
    },
  };
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

  // The header used to render while the password was still being checked,
  // so the album looked unlocked before the backend had answered.
  test('shows only a spinner while a locked album password is verified', async () => {
    let releaseImages: (value: unknown) => void = () => {};
    mockGetAlbumImages.mockImplementation(
      () =>
        new Promise((resolve) => {
          releaseImages = resolve;
        }),
    );

    const { store } = render(<AlbumDetailWithLoader />, {
      initialRoutes: [{ pathname: '/albums/a1', state: { password: 'pw' } }],
    });

    // The images request starts a render after the album loads; the loader
    // must stay up across that gap rather than flicker off.
    let loaderDropped = false;
    const unsubscribe = store.subscribe(() => {
      if (!store.getState().loader.loading) loaderDropped = true;
    });

    await waitFor(() => expect(mockGetAlbumImages).toHaveBeenCalled());
    unsubscribe();
    expect(loaderDropped).toBe(false);
    expect(store.getState().loader.loading).toBe(true);
    expect(screen.getByText('Verifying password...')).toBeInTheDocument();
    expect(screen.queryByText('Trip')).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /add images/i }),
    ).not.toBeInTheDocument();

    releaseImages({ success: true, image_ids: ['i1'] });

    await screen.findByText('Trip');
    expect(store.getState().loader.loading).toBe(false);
    expect(screen.queryByText('Verifying password...')).not.toBeInTheDocument();
  }, 30000);

  // A 401 ends loading before the redirect effect runs, which used to leave
  // one render where the album looked unlocked.
  test('never renders the album for a rejected password', async () => {
    mockGetAlbumImages.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401 },
    });

    const watcher = watchForInsertedText('Trip');

    const { store } = render(<AlbumDetailWithLoader />, {
      initialRoutes: [{ pathname: '/albums/a1', state: { password: 'wrong' } }],
    });

    await screen.findByText('Albums list');

    expect(watcher.stop()).toBe(false);
    expect(store.getState().loader.loading).toBe(false);
  }, 30000);

  // A cached result for an old password used to outlive a password change,
  // so reopening showed the album before the backend rejected it.
  test('rechecks the password when an album is reopened', async () => {
    const user = userEvent.setup();
    render(<AlbumDetailWithLoader />, {
      initialRoutes: [
        { pathname: '/albums/a1', state: { password: 'old-password' } },
      ],
    });
    await screen.findByText('Trip');

    await user.click(screen.getByRole('button', { name: /back to albums/i }));
    await screen.findByText('Albums list');

    mockGetAlbumImages.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401 },
    });
    const watcher = watchForInsertedText('Trip');

    await user.click(screen.getByRole('button', { name: 'Reopen' }));

    await waitFor(() => expect(mockGetAlbumImages).toHaveBeenCalledTimes(2));
    await screen.findByText('Albums list');
    expect(watcher.stop()).toBe(false);
  }, 30000);

  // The backend is local, but TanStack pauses queries when the machine has no
  // internet, which left the loader up with no way out.
  test('still checks the password when offline', async () => {
    const album = await mockGetAlbumById.getMockImplementation()?.();
    mockGetAlbumById.mockImplementation(async () => {
      // Go offline once the album has loaded, before the password check runs.
      onlineManager.setOnline(false);
      return album;
    });

    const { store, unmount } = render(<AlbumDetailWithLoader />, {
      initialRoutes: [{ pathname: '/albums/a1', state: { password: 'pw' } }],
    });

    try {
      expect(await screen.findByText('Trip')).toBeInTheDocument();
      expect(mockGetAlbumImages).toHaveBeenCalledWith('a1', { password: 'pw' });
      expect(store.getState().loader.loading).toBe(false);
    } finally {
      // Unmount first, so going back online resumes no queries after the test.
      unmount();
      onlineManager.setOnline(true);
    }
  }, 30000);

  // The password check never starts for a missing album, so it must not
  // leave the loader spinning forever.
  test('shows not found instead of a stuck loader for a missing album', async () => {
    mockGetAlbumById.mockRejectedValue({
      isAxiosError: true,
      response: { status: 404 },
    });
    const { store } = render(<AlbumDetailWithLoader />, {
      initialRoutes: [{ pathname: '/albums/a1', state: { password: 'pw' } }],
    });

    // usePictoQuery retries twice, 500ms apart, before the 404 settles.
    expect(
      await screen.findByText('Album not found', {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(store.getState().loader.loading).toBe(false);
  }, 30000);

  // A cached 401 used to fail the right password straight after a wrong one.
  test('opens the album with the right password after a wrong one', async () => {
    const user = userEvent.setup();
    mockGetAlbumImages.mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 401 },
    });
    render(<AlbumDetailWithLoader />, {
      initialRoutes: [{ pathname: '/albums/a1', state: { password: 'wrong' } }],
    });
    await screen.findByText('Albums list');

    await user.click(screen.getByRole('button', { name: 'Reopen' }));

    expect(await screen.findByText('Trip')).toBeInTheDocument();
    expect(mockGetAlbumImages).toHaveBeenLastCalledWith('a1', {
      password: 'old-password',
    });
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

  // Reaching a locked album without a password used to show its header
  // until the backend's 401 arrived.
  test('never renders a locked album opened without a password', async () => {
    const album = await mockGetAlbumById.getMockImplementation()?.();
    mockGetAlbumById.mockResolvedValue({
      ...album,
      data: { album: { ...album.data.album, is_locked: true } },
    });
    mockGetAlbumImages.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401 },
    });
    const watcher = watchForInsertedText('Trip');

    renderDetail();

    await screen.findByText('Albums list');
    expect(watcher.stop()).toBe(false);
  }, 30000);

  test('hides the password loader when leaving mid-check', async () => {
    mockGetAlbumImages.mockImplementation(() => new Promise(() => {}));

    const { store, unmount } = render(<AlbumDetailWithLoader />, {
      initialRoutes: [{ pathname: '/albums/a1', state: { password: 'pw' } }],
    });

    await waitFor(() => expect(mockGetAlbumImages).toHaveBeenCalled());
    expect(store.getState().loader.loading).toBe(true);

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
});
