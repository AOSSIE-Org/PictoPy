import { render, screen, waitFor, within } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import { GlobalLoader } from '@/components/Loader/GlobalLoader';
import { InfoDialog } from '@/components/Dialog/InfoDialog';
import Albums from '../Album/Album';

import { getAllAlbums, deleteAlbum } from '@/api/api-functions';

jest.mock('@/api/api-functions', () => ({
  getAllAlbums: jest.fn(),
  deleteAlbum: jest.fn(),
  createAlbum: jest.fn(),
  updateAlbum: jest.fn(),
  getAlbumImages: jest.fn(),
  addImagesToAlbum: jest.fn(),
}));

const mockGetAllAlbums = getAllAlbums as jest.Mock;
const mockDeleteAlbum = deleteAlbum as jest.Mock;

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

  beforeEach(() => {
    jest.clearAllMocks();
    document.body.style.pointerEvents = '';
    mockGetAllAlbums.mockResolvedValue({
      success: true,
      albums: [
        {
          album_id: 'a1',
          album_name: 'Trip',
          description: '',
          is_locked: false,
          cover_image_path: null,
          image_count: 3,
        },
      ],
    });
    mockDeleteAlbum.mockResolvedValue({ success: true, msg: 'deleted' });
  });

  // Deleting goes dropdown menu -> dialog. Both are Radix layers holding
  // module-level focus state, so a duplicated Radix copy in node_modules made
  // the two focus scopes trap each other and lock up the UI until reload.
  test('stays interactive after deleting an album', async () => {
    const user = userEvent.setup();
    const { store } = render(<AlbumsWithGlobalOverlays />);

    await screen.findByText('Trip');

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

    await waitFor(() => expect(mockDeleteAlbum).toHaveBeenCalled());
    expect(mockDeleteAlbum.mock.calls[0][0]).toBe('a1');

    // The success dialog is the last modal standing; dismissing it must hand
    // interactivity back to the page.
    const successDialog = await screen.findByRole('dialog');
    // The footer button and the corner X are both named "Close".
    const [closeButton] = within(successDialog).getAllByRole('button', {
      name: /close/i,
    });
    await user.click(closeButton);

    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
    );
    expect(document.body.style.pointerEvents).not.toBe('none');
    expect(store.getState().albums.albums).toHaveLength(0);
  }, 30000);
});
