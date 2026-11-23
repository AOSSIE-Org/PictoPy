import { render, screen, waitFor, within } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import { GlobalLoader } from '@/components/Loader/GlobalLoader';
import { InfoDialog } from '@/components/Dialog/InfoDialog';
import Albums from '../Album/Album';

import { getAllAlbums, deleteAlbum, getShares } from '@/api/api-functions';

jest.mock('@/api/api-functions', () => ({
  getAllAlbums: jest.fn(),
  deleteAlbum: jest.fn(),
  createAlbum: jest.fn(),
  updateAlbum: jest.fn(),
  getAlbumImages: jest.fn(),
  addImagesToAlbum: jest.fn(),
  getShares: jest.fn(),
  createShare: jest.fn(),
  revokeShare: jest.fn(),
}));

const mockGetAllAlbums = getAllAlbums as jest.Mock;
const mockDeleteAlbum = deleteAlbum as jest.Mock;
const mockGetShares = getShares as jest.Mock;

// Mirrors App.tsx, which renders the page beneath the global loader and dialog.
const AlbumsWithGlobalOverlays = () => {
  const { loading, message } = useSelector((state: RootState) => state.loader);
  const infoDialog = useSelector((state: RootState) => state.infoDialog);
  return (
    <>
      <Albums />
      <GlobalLoader loading={loading} message={message} />
      <InfoDialog
        isOpen={infoDialog.isOpen}
        title={infoDialog.title}
        message={infoDialog.message}
        variant={infoDialog.variant}
        showCloseButton={infoDialog.showCloseButton}
      />
    </>
  );
};

describe('Albums page', () => {
  beforeAll(() => {
    // Radix menus rely on these; jsdom implements none of them.
    Element.prototype.scrollIntoView = jest.fn();
    Element.prototype.hasPointerCapture = jest.fn(() => false);
    Element.prototype.setPointerCapture = jest.fn();
    Element.prototype.releasePointerCapture = jest.fn();
  });

  // Stands in for the server, so a delete is only reflected in the list once
  // the mutation actually succeeds and the query refetches.
  let serverAlbums: Record<string, unknown>[];

  beforeEach(() => {
    jest.clearAllMocks();
    document.body.style.pointerEvents = '';
    serverAlbums = [
      {
        album_id: 'a1',
        album_name: 'Trip',
        description: '',
        is_locked: false,
        cover_image_path: null,
        image_count: 3,
      },
    ];
    mockGetAllAlbums.mockImplementation(async () => ({
      success: true,
      albums: serverAlbums,
    }));
    mockDeleteAlbum.mockImplementation(async (albumId: string) => {
      serverAlbums = serverAlbums.filter((a) => a.album_id !== albumId);
      return { success: true, msg: 'deleted' };
    });
    mockGetShares.mockResolvedValue({ success: true, data: [] });
  });

  const openDeleteConfirmation = async (
    user: ReturnType<typeof userEvent.setup>,
  ) => {
    const card = screen.getByText('Trip').closest('[data-slot="card"]');
    await user.click(
      card!.querySelector('[aria-haspopup="menu"]') as HTMLElement,
    );

    const menuItems = await screen.findAllByRole('menuitem');
    const deleteItem = menuItems.find((item) =>
      /delete album/i.test(item.textContent || ''),
    );
    await user.click(deleteItem as HTMLElement);

    const confirmDialog = await screen.findByRole('dialog');
    await user.click(
      within(confirmDialog).getByRole('button', { name: /delete album/i }),
    );
  };

  const dismissResultDialog = async (
    user: ReturnType<typeof userEvent.setup>,
  ) => {
    const dialog = await screen.findByRole('dialog');
    // The footer button and the corner X are both named "Close".
    const [closeButton] = within(dialog).getAllByRole('button', {
      name: /close/i,
    });
    await user.click(closeButton);
    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
    );
  };

  // The backend withholds cover_image_path for locked albums; the card has to
  // fall back to the placeholder rather than render a broken or empty tile.
  test('shows a placeholder instead of a cover for a locked album', async () => {
    serverAlbums = [
      {
        album_id: 'a2',
        album_name: 'Private',
        description: '',
        is_locked: true,
        cover_image_path: null,
        image_count: 4,
      },
    ];

    render(<AlbumsWithGlobalOverlays />);

    const cover = await screen.findByAltText('Private');
    expect(cover.getAttribute('src')).toMatch(/placeholder-album/);
  }, 30000);

  const chooseSort = async (
    user: ReturnType<typeof userEvent.setup>,
    label: RegExp,
  ) => {
    await user.click(screen.getByRole('button', { name: /sort by/i }));
    const menuItems = await screen.findAllByRole('menuitem');
    const option = menuItems.find((item) => label.test(item.textContent || ''));
    await user.click(option as HTMLElement);
  };

  const albumOrder = () =>
    screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent);

  // 'Legacy' predates both timestamp columns, so it carries neither.
  const timestampedAlbums = [
    { album_id: 'a1', album_name: 'Legacy', image_count: 1 },
    {
      album_id: 'a2',
      album_name: 'MadeFirst',
      image_count: 1,
      created_at: '2026-07-01 10:00:00',
      updated_at: '2026-08-09 10:00:00',
    },
    {
      album_id: 'a3',
      album_name: 'MadeLast',
      image_count: 1,
      created_at: '2026-08-01 10:00:00',
      updated_at: '2026-08-02 10:00:00',
    },
  ];

  test('sorts by creation date, newest first', async () => {
    const user = userEvent.setup();
    serverAlbums = timestampedAlbums;

    render(<AlbumsWithGlobalOverlays />);
    await screen.findByText('Legacy');

    await chooseSort(user, /date created/i);

    await waitFor(() =>
      expect(albumOrder()).toEqual(['MadeLast', 'MadeFirst', 'Legacy']),
    );
  }, 30000);

  // The album made first was edited most recently, so the two date sorts must
  // not agree - otherwise this would pass against either field.
  test('sorts by last update, most recent first', async () => {
    const user = userEvent.setup();
    serverAlbums = timestampedAlbums;

    render(<AlbumsWithGlobalOverlays />);
    await screen.findByText('Legacy');

    await chooseSort(user, /recently updated/i);

    await waitFor(() =>
      expect(albumOrder()).toEqual(['MadeFirst', 'MadeLast', 'Legacy']),
    );
  }, 30000);

  test('shows skeletons while loading instead of a blocking loader', async () => {
    let releaseAlbums: (value: unknown) => void = () => {};
    mockGetAllAlbums.mockImplementation(
      () =>
        new Promise((resolve) => {
          releaseAlbums = resolve;
        }),
    );

    const { store } = render(<AlbumsWithGlobalOverlays />);

    expect(
      await screen.findAllByTestId('album-card-skeleton'),
    ).not.toHaveLength(0);
    // The empty state must not flash before the first response arrives.
    expect(screen.queryByText(/no albums/i)).not.toBeInTheDocument();
    expect(store.getState().loader.loading).toBe(false);

    releaseAlbums({ success: true, albums: serverAlbums });

    await screen.findByText('Trip');
    expect(screen.queryAllByTestId('album-card-skeleton')).toHaveLength(0);
  }, 30000);

  test('refreshes in place rather than blocking the window', async () => {
    const user = userEvent.setup();
    const { store } = render(<AlbumsWithGlobalOverlays />);

    await screen.findByText('Trip');

    let releaseRefresh: (value: unknown) => void = () => {};
    mockGetAllAlbums.mockImplementation(
      () =>
        new Promise((resolve) => {
          releaseRefresh = resolve;
        }),
    );

    await user.click(screen.getByRole('button', { name: /refresh/i }));

    // The grid stays on screen and only the button reports the work.
    const refreshButton = await screen.findByRole('button', {
      name: /refreshing/i,
    });
    expect(refreshButton).toBeDisabled();
    expect(screen.getByText('Trip')).toBeInTheDocument();
    expect(store.getState().loader.loading).toBe(false);

    releaseRefresh({ success: true, albums: serverAlbums });

    await screen.findByRole('button', { name: /^refresh$/i });
  }, 30000);

  // Deleting goes dropdown menu -> dialog. Both are Radix layers holding
  // module-level focus state, so a duplicated Radix copy in node_modules made
  // the two focus scopes trap each other and lock up the UI until reload.
  test('stays interactive after deleting an album', async () => {
    const user = userEvent.setup();
    const { store } = render(<AlbumsWithGlobalOverlays />);

    await screen.findByText('Trip');
    await openDeleteConfirmation(user);

    await waitFor(() => expect(mockDeleteAlbum).toHaveBeenCalled());
    expect(mockDeleteAlbum.mock.calls[0][0]).toBe('a1');

    // The success dialog is the last modal standing; dismissing it must hand
    // interactivity back to the page.
    await dismissResultDialog(user);

    expect(document.body.style.pointerEvents).not.toBe('none');
    await waitFor(() => expect(store.getState().albums.albums).toHaveLength(0));
  }, 30000);

  test('refetches the list so a deleted album does not linger', async () => {
    const user = userEvent.setup();
    render(<AlbumsWithGlobalOverlays />);

    await screen.findByText('Trip');
    await openDeleteConfirmation(user);
    await dismissResultDialog(user);

    // The mutation invalidates ['albums'], so the list comes back from the
    // server rather than from a local guess about what the delete did.
    expect(mockGetAllAlbums.mock.calls.length).toBeGreaterThan(1);
    await waitFor(() =>
      expect(screen.queryByText('Trip')).not.toBeInTheDocument(),
    );
  }, 30000);

  test('keeps the album when the delete fails', async () => {
    mockDeleteAlbum.mockRejectedValue(new Error('boom'));

    const user = userEvent.setup();
    const { store } = render(<AlbumsWithGlobalOverlays />);

    await screen.findByText('Trip');
    await openDeleteConfirmation(user);

    // usePictoMutation retries twice with a 500ms backoff before it reports
    // failure, which is already past findBy's default one second wait.
    const errorDialog = await screen.findByRole('dialog', undefined, {
      timeout: 5000,
    });
    expect(within(errorDialog).getByText('Error')).toBeInTheDocument();

    // Only the error dialog may be open — the confirmation must not still be
    // sitting underneath it.
    expect(screen.getAllByRole('dialog')).toHaveLength(1);

    await dismissResultDialog(user);

    expect(document.body.style.pointerEvents).not.toBe('none');
    expect(store.getState().albums.albums).toHaveLength(1);
    expect(screen.getByText('Trip')).toBeInTheDocument();
  }, 30000);
});
