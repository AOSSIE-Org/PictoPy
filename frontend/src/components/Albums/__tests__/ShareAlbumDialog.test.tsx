import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/test-utils';
import { createShare, revokeShare } from '@/api/api-functions';
import { openUrl } from '@tauri-apps/plugin-opener';
import { startTunnel, stopTunnel, tunnelStatus } from '@/utils/tunnel';
import { Album } from '@/types/Album';
import { Share } from '@/types/Share';
import { ShareAlbumDialog } from '../ShareAlbumDialog';

jest.mock('@/api/api-functions', () => ({
  createShare: jest.fn(),
  revokeShare: jest.fn(),
}));

jest.mock('@tauri-apps/plugin-opener', () => ({
  openUrl: jest.fn(),
}));

jest.mock('@/utils/tunnel', () => ({
  startTunnel: jest.fn(),
  stopTunnel: jest.fn(),
  tunnelStatus: jest.fn(),
}));

const mockCreateShare = createShare as jest.Mock;
const mockRevokeShare = revokeShare as jest.Mock;
const mockStartTunnel = startTunnel as jest.Mock;
const mockStopTunnel = stopTunnel as jest.Mock;
const mockTunnelStatus = tunnelStatus as jest.Mock;
const mockOpenUrl = openUrl as jest.Mock;

const internetToggle = () => screen.getByRole('radio', { name: /internet/i });

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
    mockStartTunnel.mockResolvedValue('https://abc123.lhr.life');
    mockStopTunnel.mockResolvedValue(undefined);
    mockTunnelStatus.mockResolvedValue(null);
    mockOpenUrl.mockResolvedValue(undefined);
  });

  describe('internet mode', () => {
    it('shares on the local network unless asked otherwise', async () => {
      const user = userEvent.setup();
      renderDialog();

      await user.click(screen.getByRole('button', { name: /start sharing/i }));

      await waitFor(() => expect(mockCreateShare).toHaveBeenCalled());
      expect(mockStartTunnel).not.toHaveBeenCalled();
    });

    it('asks for a password by default once the link leaves the network', async () => {
      const user = userEvent.setup();
      renderDialog();

      expect(
        screen.getByRole('switch', { name: /require a password/i }),
      ).not.toBeChecked();

      await user.click(internetToggle());

      expect(
        screen.getByRole('switch', { name: /require a password/i }),
      ).toBeChecked();
      expect(screen.getByText(/link leaves your network/i)).toBeInTheDocument();
      expect(
        screen.getByText(/fetch links automatically/i),
      ).toBeInTheDocument();
    });

    it('opens a tunnel and shows only that address', async () => {
      const user = userEvent.setup();
      renderDialog();

      await user.click(internetToggle());
      await user.click(
        screen.getByRole('switch', { name: /require a password/i }),
      );
      await user.click(screen.getByRole('button', { name: /start sharing/i }));

      await waitFor(() => expect(mockStartTunnel).toHaveBeenCalledWith(52125));
      expect(await screen.findByLabelText('Link')).toHaveValue(
        'https://abc123.lhr.life/s/tok-1',
      );
      // The LAN addresses would only work inside the house, so offering them
      // alongside the link the user asked for would be misleading.
      expect(screen.queryByText('192.168.1.5')).not.toBeInTheDocument();
    });

    it('undoes the share when no tunnel can be opened', async () => {
      const user = userEvent.setup();
      mockStartTunnel.mockRejectedValue('no provider answered.');
      renderDialog();

      await user.click(internetToggle());
      await user.click(
        screen.getByRole('switch', { name: /require a password/i }),
      );
      await user.click(screen.getByRole('button', { name: /start sharing/i }));

      expect(
        await screen.findByText(/could not open a connection/i),
      ).toBeInTheDocument();
      // Leaving a share the user did not get would be worse than none at all.
      await waitFor(() =>
        expect(mockRevokeShare).toHaveBeenCalledWith('tok-1'),
      );
      expect(screen.queryByLabelText('Link')).not.toBeInTheDocument();
    });

    it('points the help button at whichever mode is selected', async () => {
      const user = userEvent.setup();
      renderDialog();

      await user.click(
        screen.getByRole('button', { name: /how sharing works/i }),
      );
      expect(mockOpenUrl).toHaveBeenLastCalledWith(
        'https://aossie-org.github.io/PictoPy/overview/sharing-albums/',
      );

      await user.click(internetToggle());
      await user.click(
        screen.getByRole('button', { name: /how sharing works/i }),
      );
      // Someone weighing up internet mode should land on what it costs.
      expect(mockOpenUrl).toHaveBeenLastCalledWith(
        'https://aossie-org.github.io/PictoPy/overview/sharing-albums/#internet-mode',
      );
    });

    // Failing quietly would leave nothing on screen and no way to reach the
    // page, which is how a missing capability presented in the running app.
    it('hands over the address when the browser cannot be opened', async () => {
      const user = userEvent.setup();
      mockOpenUrl.mockRejectedValue(new Error('opener.open_url not allowed'));
      const { store } = renderDialog();

      await user.click(
        screen.getByRole('button', { name: /how sharing works/i }),
      );

      await waitFor(() =>
        expect(store.getState().infoDialog.isOpen).toBe(true),
      );
      expect(store.getState().infoDialog.message).toContain(
        'https://aossie-org.github.io/PictoPy/overview/sharing-albums/',
      );
    });

    it('closes the tunnel when the share is stopped', async () => {
      const user = userEvent.setup();
      mockTunnelStatus.mockResolvedValue('https://abc123.lhr.life');
      renderDialog([share]);

      await waitFor(() =>
        expect(screen.getByLabelText('Link')).toHaveValue(
          'https://abc123.lhr.life/s/tok-1',
        ),
      );
      await user.click(screen.getByRole('button', { name: /stop sharing/i }));

      await waitFor(() => expect(mockStopTunnel).toHaveBeenCalled());
    });
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
