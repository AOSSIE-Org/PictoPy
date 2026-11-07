import userEvent from '@testing-library/user-event';
import { render, screen } from '@/test-utils';
import { useFolder } from '@/hooks/useFolder';
import { FolderSetupStep } from '../FolderSetupStep';

// The component's "@/App.css" import resolves through the "@/(.*)" alias
// before jest's css moduleNameMapper rule gets a chance at it, so jest tries
// to parse the raw stylesheet as JS. Stub it directly, same as the css rule
// would, rather than touching the shared jest config for one test file.
jest.mock('@/App.css', () => ({}));

jest.mock('@/hooks/useFolder', () => ({
  useFolder: jest.fn(),
}));

const mockUseFolder = useFolder as jest.Mock;

const renderStep = () =>
  render(
    <FolderSetupStep stepIndex={0} totalSteps={3} currentStepDisplayIndex={0} />,
  );

describe('FolderSetupStep', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('shows the folder name, not the whole path, for a Windows-style selection', async () => {
    const user = userEvent.setup();
    mockUseFolder.mockReturnValue({
      pickSingleFolder: jest
        .fn()
        .mockResolvedValue('C:\\Users\\me\\Pictures\\Vacation'),
      addFolderMutate: jest.fn(),
    });

    renderStep();
    await user.click(screen.getByText(/click to select a folder/i));

    expect(await screen.findByText('Vacation')).toBeInTheDocument();
  });
});
