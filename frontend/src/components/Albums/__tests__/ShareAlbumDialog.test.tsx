import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/test-utils';
import { createShare, revokeShare } from '@/api/api-functions';
import { Album } from '@/types/Album';
import { Share } from '@/types/Share';
import { ShareAlbumDialog } from '../ShareAlbumDialog';

jest.mock('@/api/api-functions', () => ({
  createShare: jest.fn(),
  revokeShare: jest.fn(),
}));

const mockCreateShare = createShare as jest.Mock;
const mockRevokeShare = revokeShare as jest.Mock;

const album: Album = {
  id: 'a1',
  name: 'Trip to Goa',
  description: '',
  is_locked: false,
  image_count: 2,
  created_at: null,
  updated_at: null,
};

const share: Share = {
  token: 'tok-1',
  album_id: 'a1',
  album_name: 'Trip to Goa',
  image_count: 2,
  port: 52125,
  created_at: '2026-08-07T10:00:00+00:00',
  expires_at: null,
  is_protected: false,
  urls: [
    {
      interface: 'Wi-Fi',
      ip: '192.168.1.5',
      url: 'http://192.168.1.5:52125/s/tok-1',
    },
    {
      interface: 'Ethernet',
      ip: '10.0.0.4',
      url: 'http://10.0.0.4:52125/s/tok-1',
    },
  ],
};

const renderDialog = (existing: Share[] = [], onChanged = jest.fn()) =>
  render(
    <ShareAlbumDialog
      album={album}
      shares={existing}
      isOpen={true}
      onClose={jest.fn()}
      onChanged={onChanged}
    />,
  );

describe('ShareAlbumDialog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateShare.mockResolvedValue({ success: true, data: share });
    mockRevokeShare.mockResolvedValue({ success: true });
  });

  it('shares without a password by default', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByRole('button', { name: /start sharing/i }));

    await waitFor(() => expect(mockCreateShare).toHaveBeenCalled());
    expect(mockCreateShare).toHaveBeenCalledWith('a1', {
      expires_in_minutes: 1440,
    });
  });

  it('sends the password when one is asked for', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(
      screen.getByRole('switch', { name: /require a password/i }),
    );
    await user.type(screen.getByLabelText('Password'), 'beach-house');
    await user.click(screen.getByRole('button', { name: /start sharing/i }));

    await waitFor(() => expect(mockCreateShare).toHaveBeenCalled());
    expect(mockCreateShare).toHaveBeenCalledWith('a1', {
      expires_in_minutes: 1440,
      password: 'beach-house',
    });
  });

  it('refuses a password the backend would reject', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(
      screen.getByRole('switch', { name: /require a password/i }),
    );
    await user.type(screen.getByLabelText('Password'), 'ab');
    await user.click(screen.getByRole('button', { name: /start sharing/i }));

    expect(
      await screen.findByText(/at least 4 characters/i),
    ).toBeInTheDocument();
    expect(mockCreateShare).not.toHaveBeenCalled();
  });

  it('drops the expiry when the share should last until stopped', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByRole('radio', { name: /until i stop it/i }));
    await user.click(screen.getByRole('button', { name: /start sharing/i }));

    await waitFor(() => expect(mockCreateShare).toHaveBeenCalledWith('a1', {}));
  });

  it('shows the link once the share exists', async () => {
    renderDialog([share]);

    expect(screen.getByLabelText('Link')).toHaveValue(
      'http://192.168.1.5:52125/s/tok-1',
    );
  });

  it('switches the link to another address', async () => {
    const user = userEvent.setup();
    renderDialog([share]);

    await user.click(screen.getByRole('button', { name: /ethernet/i }));

    expect(screen.getByLabelText('Link')).toHaveValue(
      'http://10.0.0.4:52125/s/tok-1',
    );
  });

  it('says so when the machine has no network address', () => {
    renderDialog([{ ...share, urls: [] }]);

    expect(
      screen.getByText(/no local network address was found/i),
    ).toBeInTheDocument();
  });

  it('revokes the share and tells the parent', async () => {
    const user = userEvent.setup();
    const onChanged = jest.fn();
    renderDialog([share], onChanged);

    await user.click(screen.getByRole('button', { name: /stop sharing/i }));

    await waitFor(() => expect(mockRevokeShare).toHaveBeenCalledWith('tok-1'));
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
  });

  // Creating a share leaves earlier ones valid, so stopping has to take down
  // every token or the album stays reachable after the UI says it stopped.
  it('stops every share the album has, not just the newest', async () => {
    const user = userEvent.setup();
    const older: Share = { ...share, token: 'tok-0' };
    renderDialog([share, older]);

    await user.click(screen.getByRole('button', { name: /stop sharing/i }));

    await waitFor(() => expect(mockRevokeShare).toHaveBeenCalledTimes(2));
    expect(mockRevokeShare).toHaveBeenCalledWith('tok-1');
    expect(mockRevokeShare).toHaveBeenCalledWith('tok-0');
  });

  it('stops the share it just created along with any earlier one', async () => {
    const user = userEvent.setup();
    const older: Share = { ...share, token: 'tok-0' };
    mockCreateShare.mockResolvedValue({
      success: true,
      data: { ...share, token: 'tok-new' },
    });
    const { rerender } = renderDialog([]);

    await user.click(screen.getByRole('button', { name: /start sharing/i }));
    await screen.findByLabelText('Link');

    // What the parent does after the refetch: it hands down the shares the
    // backend knows about, which need not yet include the one just made.
    rerender(
      <ShareAlbumDialog
        album={album}
        shares={[older]}
        isOpen={true}
        onClose={jest.fn()}
        onChanged={jest.fn()}
      />,
    );

    await user.click(screen.getByRole('button', { name: /stop sharing/i }));

    await waitFor(() => expect(mockRevokeShare).toHaveBeenCalledTimes(2));
    expect(mockRevokeShare).toHaveBeenCalledWith('tok-new');
    expect(mockRevokeShare).toHaveBeenCalledWith('tok-0');
  });
});
