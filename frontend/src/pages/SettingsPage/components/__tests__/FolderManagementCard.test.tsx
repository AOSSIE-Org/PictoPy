import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';

import FolderManagementCard from '../FolderManagementCard';
import type { FolderDetails } from '@/types/Folder';

const mockDeleteFolder = jest.fn();

const folder = (id: string, parent?: string): FolderDetails => ({
  folder_id: id,
  folder_path: `/${id}`,
  parent_folder_id: parent,
  last_modified_time: 0,
  AI_Tagging: false,
});

// /parent has one subfolder, /solo has none.
const mockFolders = [
  folder('parent'),
  folder('child', 'parent'),
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

    expect(screen.getByText('Also delete 1 subfolder')).toBeInTheDocument();
    expect(mockDeleteFolder).not.toHaveBeenCalled();
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
    expect(screen.getByLabelText('Also delete 1 subfolder')).toBeChecked();
    await confirmDelete(user);

    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', false);
  });

  it('remembers the choice made in the dialog as the new default', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText('Also delete 1 subfolder'));
    await confirmDelete(user);

    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', false);
    expect(localStorage.getItem('pictopy:deleteSubfolders')).toBe('true');
  });

  it('cancelling deletes nothing and changes no setting', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText('Also delete 1 subfolder'));
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
      screen.queryByText('Also delete 1 subfolder'),
    ).not.toBeInTheDocument();
    expect(mockDeleteFolder).toHaveBeenCalledWith('parent', true);
  });

  it('shows the dialog again once the default has changed', async () => {
    const user = userEvent.setup();
    render(<FolderManagementCard />);

    await clickDelete(user, '/parent');
    await user.click(screen.getByLabelText("Don't show again"));
    await confirmDelete(user);
    mockDeleteFolder.mockClear();

    // e.g. the Settings switch flipped to "delete subfolders"
    localStorage.setItem('pictopy:deleteSubfolders', 'true');
    await clickDelete(user, '/parent');

    expect(screen.getByText('Also delete 1 subfolder')).toBeInTheDocument();
    expect(mockDeleteFolder).not.toHaveBeenCalled();
  });
});
