import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import FolderManagementCard from '@/pages/SettingsPage/components/FolderManagementCard';
import { FolderDetails } from '@/types/Folder';

const mockDeleteFolders = jest.fn();
const mockToggleAITagging = jest.fn();

const mockMakeFolder = (id: string, path: string): FolderDetails => ({
  folder_id: id,
  folder_path: path,
  last_modified_time: 0,
  AI_Tagging: false,
  indexing_status: 'completed',
});

const mockFolders: FolderDetails[] = [
  mockMakeFolder('folder-1', 'C:\\Users\\me\\Pictures\\Holiday'),
  mockMakeFolder('folder-2', 'C:\\Users\\me\\Pictures\\Screenshots'),
  mockMakeFolder('folder-3', 'C:\\Users\\me\\Pictures\\Camera'),
];

jest.mock('@/hooks/useFolderOperations', () => ({
  useFolderOperations: () => ({
    folders: mockFolders,
    toggleAITagging: mockToggleAITagging,
    deleteFolders: mockDeleteFolders,
    enableAITaggingPending: false,
    disableAITaggingPending: false,
    deleteFoldersPending: false,
  }),
}));

jest.mock('@/hooks/useLibraryProcessingStatus', () => ({
  useLibraryProcessingStatus: () => ({ semanticAvailable: true }),
}));

jest.mock('@/components/FolderPicker/FolderPicker', () => ({
  __esModule: true,
  default: () => <div data-testid="folder-picker" />,
}));

const SINGLE_TITLE = 'Delete this folder?';

const setup = () => {
  const user = userEvent.setup();
  render(<FolderManagementCard />);
  return { user };
};

const deleteButtonFor = (folder: FolderDetails) =>
  screen.getByRole('button', { name: `Delete folder ${folder.folder_path}` });

const checkboxFor = (folder: FolderDetails) =>
  screen.getByRole('checkbox', { name: `Select folder ${folder.folder_path}` });

beforeEach(() => {
  jest.clearAllMocks();
});

describe('FolderManagementCard - single folder deletion', () => {
  test('no confirmation is shown until a delete button is clicked', () => {
    setup();

    expect(screen.queryByText(SINGLE_TITLE)).not.toBeInTheDocument();
  });

  test('clicking delete asks for confirmation instead of deleting straight away', async () => {
    const { user } = setup();

    await user.click(deleteButtonFor(mockFolders[0]));

    expect(screen.getByText(SINGLE_TITLE)).toBeInTheDocument();
    expect(mockDeleteFolders).not.toHaveBeenCalled();
  });

  test('the confirmation names the folder and warns that it cannot be undone', async () => {
    const { user } = setup();

    await user.click(deleteButtonFor(mockFolders[0]));

    const description = screen.getByText(/cannot be undone/i);
    expect(description).toHaveTextContent(mockFolders[0].folder_path);
    expect(description).toHaveTextContent(/stay on your disk/i);
  });

  test('cancelling closes the confirmation and deletes nothing', async () => {
    const { user } = setup();

    await user.click(deleteButtonFor(mockFolders[0]));
    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(mockDeleteFolders).not.toHaveBeenCalled();
    expect(screen.queryByText(SINGLE_TITLE)).not.toBeInTheDocument();
  });

  test('confirming deletes the folder and closes the confirmation', async () => {
    const { user } = setup();

    await user.click(deleteButtonFor(mockFolders[0]));
    await user.click(screen.getByRole('button', { name: /^delete folder$/i }));

    expect(mockDeleteFolders).toHaveBeenCalledTimes(1);
    expect(mockDeleteFolders).toHaveBeenCalledWith([mockFolders[0].folder_id]);
    expect(screen.queryByText(SINGLE_TITLE)).not.toBeInTheDocument();
  });

  test('confirming deletes the folder whose delete button was clicked', async () => {
    const { user } = setup();

    await user.click(deleteButtonFor(mockFolders[1]));
    await user.click(screen.getByRole('button', { name: /^delete folder$/i }));

    expect(mockDeleteFolders).toHaveBeenCalledWith([mockFolders[1].folder_id]);
  });

  test('the confirmation can be reopened after cancelling', async () => {
    const { user } = setup();

    await user.click(deleteButtonFor(mockFolders[0]));
    await user.click(screen.getByRole('button', { name: /cancel/i }));
    await user.click(deleteButtonFor(mockFolders[0]));

    expect(screen.getByText(SINGLE_TITLE)).toBeInTheDocument();
    expect(mockDeleteFolders).not.toHaveBeenCalled();
  });
});

describe('FolderManagementCard - bulk deletion', () => {
  test('the bulk delete button only appears once something is selected', async () => {
    const { user } = setup();

    expect(
      screen.queryByRole('button', { name: /delete selected/i }),
    ).not.toBeInTheDocument();

    await user.click(checkboxFor(mockFolders[0]));

    expect(
      screen.getByRole('button', { name: /delete selected \(1\)/i }),
    ).toBeInTheDocument();
  });

  test('the bulk delete button counts the selected folders', async () => {
    const { user } = setup();

    await user.click(checkboxFor(mockFolders[0]));
    await user.click(checkboxFor(mockFolders[2]));

    expect(
      screen.getByRole('button', { name: /delete selected \(2\)/i }),
    ).toBeInTheDocument();
  });

  test('unselecting a folder updates the count and hides the button at zero', async () => {
    const { user } = setup();

    await user.click(checkboxFor(mockFolders[0]));
    await user.click(checkboxFor(mockFolders[0]));

    expect(
      screen.queryByRole('button', { name: /delete selected/i }),
    ).not.toBeInTheDocument();
  });

  test('bulk deletion asks for one confirmation naming the count', async () => {
    const { user } = setup();

    await user.click(checkboxFor(mockFolders[0]));
    await user.click(checkboxFor(mockFolders[1]));
    await user.click(
      screen.getByRole('button', { name: /delete selected \(2\)/i }),
    );

    expect(screen.getByText('Delete 2 folders?')).toBeInTheDocument();
    expect(screen.getByText(/cannot be undone/i)).toHaveTextContent(
      '2 folders will be removed',
    );
    expect(mockDeleteFolders).not.toHaveBeenCalled();
  });

  test('confirming a bulk deletion removes every selected folder in one call', async () => {
    const { user } = setup();

    await user.click(checkboxFor(mockFolders[0]));
    await user.click(checkboxFor(mockFolders[2]));
    await user.click(
      screen.getByRole('button', { name: /delete selected \(2\)/i }),
    );
    await user.click(
      screen.getByRole('button', { name: /^delete 2 folders$/i }),
    );

    expect(mockDeleteFolders).toHaveBeenCalledTimes(1);
    expect(mockDeleteFolders).toHaveBeenCalledWith([
      mockFolders[0].folder_id,
      mockFolders[2].folder_id,
    ]);
  });

  test('cancelling a bulk deletion keeps the selection and deletes nothing', async () => {
    const { user } = setup();

    await user.click(checkboxFor(mockFolders[0]));
    await user.click(checkboxFor(mockFolders[1]));
    await user.click(
      screen.getByRole('button', { name: /delete selected \(2\)/i }),
    );
    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(mockDeleteFolders).not.toHaveBeenCalled();
    expect(
      screen.getByRole('button', { name: /delete selected \(2\)/i }),
    ).toBeInTheDocument();
  });

  test('select all picks every folder, and unselects them again', async () => {
    const { user } = setup();
    const selectAll = screen.getByRole('checkbox', { name: /select all/i });

    await user.click(selectAll);

    expect(
      screen.getByRole('button', { name: /delete selected \(3\)/i }),
    ).toBeInTheDocument();

    await user.click(selectAll);

    expect(
      screen.queryByRole('button', { name: /delete selected/i }),
    ).not.toBeInTheDocument();
  });

  test('selecting every folder individually ticks the select all box', async () => {
    const { user } = setup();

    for (const folder of mockFolders) {
      await user.click(checkboxFor(folder));
    }

    expect(screen.getByRole('checkbox', { name: /select all/i })).toBeChecked();
  });
});
