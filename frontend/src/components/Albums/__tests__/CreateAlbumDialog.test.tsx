import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/test-utils';
import { createAlbum } from '@/api/api-functions';
import { CreateAlbumDialog } from '../CreateAlbumDialog';

jest.mock('@/api/api-functions', () => ({
  createAlbum: jest.fn(),
}));

const mockCreateAlbum = createAlbum as jest.Mock;

const renderDialog = (
  isOpen = true,
  onClose = jest.fn(),
  onSuccess = jest.fn(),
) =>
  render(
    <CreateAlbumDialog
      isOpen={isOpen}
      onClose={onClose}
      onSuccess={onSuccess}
    />,
  );

describe('CreateAlbumDialog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateAlbum.mockResolvedValue({
      success: true,
      data: { id: 'a1', name: 'New Album' },
    });
  });

  it('renders the dialog when isOpen is true', () => {
    renderDialog(true);
    expect(
      screen.getByRole('heading', { name: /create new album/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/album name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/lock album/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/^password/i)).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText(/confirm password/i),
    ).not.toBeInTheDocument();
  });

  it('shows error if album name is empty on submission', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByRole('button', { name: /create album/i }));

    expect(screen.getByText('Album name is required')).toBeInTheDocument();
    expect(mockCreateAlbum).not.toHaveBeenCalled();
  });

  it('reveals password and confirm password inputs when lock album is toggled on', async () => {
    const user = userEvent.setup();
    renderDialog();

    expect(screen.queryByLabelText(/^password/i)).not.toBeInTheDocument();

    await user.click(screen.getByLabelText(/lock album/i));

    expect(screen.getByLabelText(/^password \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password \*/i)).toBeInTheDocument();
  });

  it('toggles password and confirm password visibility', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.click(screen.getByLabelText(/lock album/i));

    const passwordInput = screen.getByLabelText(/^password \*/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password \*/i);
    const togglePasswordBtn = screen.getByRole('button', {
      name: /show password/i,
    });
    const toggleConfirmBtn = screen.getByRole('button', {
      name: /show confirm password/i,
    });

    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(confirmPasswordInput).toHaveAttribute('type', 'password');

    // Toggle password visibility
    await user.click(togglePasswordBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(
      screen.getByRole('button', { name: /hide password/i }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /hide password/i }));
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Toggle confirm password visibility
    await user.click(toggleConfirmBtn);
    expect(confirmPasswordInput).toHaveAttribute('type', 'text');
    expect(
      screen.getByRole('button', { name: /hide confirm password/i }),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole('button', { name: /hide confirm password/i }),
    );
    expect(confirmPasswordInput).toHaveAttribute('type', 'password');
  });

  it('validates password requirement when lock album is enabled', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.type(screen.getByLabelText(/album name/i), 'Family Trip');
    await user.click(screen.getByLabelText(/lock album/i));

    // Submit with both password and confirm password empty
    await user.click(screen.getByRole('button', { name: /create album/i }));

    expect(
      screen.getByText('Password is required for locked albums'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Confirm password is required'),
    ).toBeInTheDocument();
    expect(mockCreateAlbum).not.toHaveBeenCalled();
  });

  it('validates that confirm password is required if password is entered', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.type(screen.getByLabelText(/album name/i), 'Family Trip');
    await user.click(screen.getByLabelText(/lock album/i));
    await user.type(screen.getByLabelText(/^password \*/i), 'securepass123');

    await user.click(screen.getByRole('button', { name: /create album/i }));

    expect(
      screen.getByText('Confirm password is required'),
    ).toBeInTheDocument();
    expect(mockCreateAlbum).not.toHaveBeenCalled();
  });

  it('validates that passwords must match', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.type(screen.getByLabelText(/album name/i), 'Family Trip');
    await user.click(screen.getByLabelText(/lock album/i));
    await user.type(screen.getByLabelText(/^password \*/i), 'securepass123');
    await user.type(
      screen.getByLabelText(/confirm password \*/i),
      'differentpass',
    );

    await user.click(screen.getByRole('button', { name: /create album/i }));

    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    expect(mockCreateAlbum).not.toHaveBeenCalled();
  });

  it('submits locked album successfully when passwords match', async () => {
    const user = userEvent.setup();
    renderDialog(true, jest.fn(), jest.fn());

    await user.type(screen.getByLabelText(/album name/i), 'Secret Album');
    await user.type(screen.getByLabelText(/description/i), 'Secret photos');
    await user.click(screen.getByLabelText(/lock album/i));
    await user.type(screen.getByLabelText(/^password \*/i), 'secret123');
    await user.type(screen.getByLabelText(/confirm password \*/i), 'secret123');

    await user.click(screen.getByRole('button', { name: /create album/i }));

    await waitFor(() => {
      expect(mockCreateAlbum).toHaveBeenCalledWith({
        name: 'Secret Album',
        description: 'Secret photos',
        is_locked: true,
        password: 'secret123',
      });
    });
  });

  it('submits unlocked album without password payload', async () => {
    const user = userEvent.setup();
    renderDialog();

    await user.type(screen.getByLabelText(/album name/i), 'Public Album');
    await user.click(screen.getByRole('button', { name: /create album/i }));

    await waitFor(() => {
      expect(mockCreateAlbum).toHaveBeenCalledWith({
        name: 'Public Album',
        is_locked: false,
      });
    });
  });

  it('calls onClose when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = jest.fn();
    renderDialog(true, handleClose);

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
