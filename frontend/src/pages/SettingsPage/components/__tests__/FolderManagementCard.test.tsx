import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';

import FolderManagementCard from '../FolderManagementCard';
import { Switch } from '@/components/ui/switch';
import { useDeleteSubfoldersPreference } from '@/hooks/useDeleteSubfoldersPreference';
import type { FolderDetails } from '@/types/Folder';

const mockDeleteFolder = jest.fn();

const folder = (id: string, parent?: string): FolderDetails => ({
  folder_id: id,
  folder_path: `/${id}`,
  parent_folder_id: parent,
  last_modified_time: 0,
  AI_Tagging: false,
});

// /parent has two subfolders (a child and a grandchild), /solo has none.
const mockFolders = [
  folder('parent'),
  folder('child', 'parent'),
  folder('grandchild', 'child'),
  folder('solo'),
];

jest.mock('@/hooks/useFolderOperations', () => ({
  useFolderOperations: () => ({
    folders: mockFolders,
    toggleAITagging: jest.fn(),
    deleteFolder: mockDeleteFolder,
    enableAITaggingPending: false,
    disableAITaggingPending: false,
    deleteFolderPending: false,
  }),
}));
jest.mock('@/hooks/useLibraryProcessingStatus', () => ({
  useLibraryProcessingStatus: () => ({ semanticAvailable: false }),
}));
jest.mock('@/components/FolderPicker/FolderPicker', () => () => null);

// Wired like the "Delete Subfolders" switch in UserPreferencesCard, through the
// real hook, so tests change the setting the way a user does in Settings.
const SettingsSwitch = () => {
  const { deleteSubfolders, setDeleteSubfolders } =
    useDeleteSubfoldersPreference();
  return (
    <Switch
      aria-label="Delete Subfolders"
      checked={deleteSubfolders}
      onCheckedChange={setDeleteSubfolders}
    />
  );
};

const renderWithSettings = () =>
  render(
    <>
      <SettingsSwitch />
      <FolderManagementCard />
    </>,
  );

const clickDelete = (user: ReturnType<typeof userEvent.setup>, path: string) =>
  user.click(screen.getByRole('button', { name: `Delete folder ${path}` }));

const confirmDelete = (user: ReturnType<typeof userEvent.setup>) =>
  user.click(screen.getByRole('button', { name: 'Delete' }));

beforeEach(() => {
  localStorage.clear();
  mockDeleteFolder.mockClear();
});

describe('FolderManagementCard folder deletion', () => {
  it('deletes a folder without subfolders straight away', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/solo');

    expect(mockDeleteFolder).toHaveBeenCalledWith('solo');
    expect(screen.queryByText('Delete folder')).not.toBeInTheDocument();
  });

  it('asks first when the folder has subfolders', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');

    expect(screen.getByText('Also delete 2 subfolders')).toBeInTheDocument();
    expect(mockDeleteFolder).not.toHaveBeenCalled();
  });

  it('counts nested subfolders, not just direct children', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    // /child has a single subfolder (the grandchild); /parent has two levels.
    await clickDelete(user, '/child');
    expect(screen.getByText('Also delete 1 subfolder')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    await clickDelete(user, '/parent');
    expect(screen.getByText('Also delete 2 subfolders')).toBeInTheDocument();
  });

  it('keeps subfolders by default', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    await confirmDelete(user);

    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', true);
  });

  it('deletes subfolders when the Settings default is on', async () => {
    localStorage.setItem('pictopy:deleteSubfolders', 'true');
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    expect(screen.getByLabelText('Also delete 2 subfolders')).toBeChecked();
    await confirmDelete(user);

    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', false);
  });

  it('remembers the choice made in the dialog as the new default', async () => {
    const user = userEvent.setup();
    renderWithSettings();

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText('Also delete 2 subfolders'));
    await confirmDelete(user);

    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', false);
    expect(localStorage.getItem('pictopy:deleteSubfolders')).toBe('true');
    // the mounted Settings switch follows the new default
    expect(
      screen.getByRole('switch', { name: 'Delete Subfolders' }),
    ).toBeChecked();
  });

  it('cancelling deletes nothing and changes no setting', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText('Also delete 2 subfolders'));
    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(mockDeleteFolder).not.toHaveBeenCalled();
    expect(localStorage.getItem('pictopy:deleteSubfolders')).toBeNull();
  });

  it('skips the dialog after "Don\'t show again" and uses the default', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText("Don't show again"));
    await confirmDelete(user);
    mockDeleteFolder.mockClear();

    await clickDelete(user, '/parent');

    // No dialog; the saved default (keep subfolders) is applied directly.
    expect(
      screen.queryByText('Also delete 2 subfolders'),
    ).not.toBeInTheDocument();
    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', true);
  });

  it('shows the dialog again after the Settings switch is flipped', async () => {
    const user = userEvent.setup();
    renderWithSettings();

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText("Don't show again"));
    await confirmDelete(user);
    mockDeleteFolder.mockClear();

    // the user flips "Delete Subfolders" in Settings
    await user.click(screen.getByRole('switch', { name: 'Delete Subfolders' }));
    await clickDelete(user, '/parent');

    expect(screen.getByLabelText('Also delete 2 subfolders')).toBeChecked();
    expect(mockDeleteFolder).not.toHaveBeenCalled();
  });

  it('does not grant "Don\'t show again" when the new default fails to save', async () => {
    // saved default is "delete subfolders"; only that write will fail
    localStorage.setItem('pictopy:deleteSubfolders', 'true');
    const realSetItem = Storage.prototype.setItem;
    const setItemSpy = jest
      .spyOn(Storage.prototype, 'setItem')
      .mockImplementation(function (this: Storage, key: string, value: string) {
        if (key === 'pictopy:deleteSubfolders') throw new Error('quota');
        return realSetItem.call(this, key, value);
      });
    const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText('Also delete 2 subfolders')); // keep
    await user.click(screen.getByLabelText("Don't show again"));
    await confirmDelete(user);

    // this deletion still follows what was chosen in the dialog
    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', true);
    mockDeleteFolder.mockClear();

    await clickDelete(user, '/parent');

    // the old "delete subfolders" default must not apply without asking
    expect(
      screen.getByLabelText('Also delete 2 subfolders'),
    ).toBeInTheDocument();
    expect(mockDeleteFolder).not.toHaveBeenCalled();
    expect(
      localStorage.getItem('pictopy:skipFolderDeleteConfirmation'),
    ).toBeNull();

    setItemSpy.mockRestore();
    errorSpy.mockRestore();
  });
});
