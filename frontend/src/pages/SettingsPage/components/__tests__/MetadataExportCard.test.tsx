import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';

import MetadataExportCard, {
  describeExportStatus,
} from '../MetadataExportCard';
import type { MetadataExportStatus } from '@/api/api-functions/metadata_export';

const mockStartMetadataExport = jest.fn();
const mockGetMetadataExportStatus = jest.fn();
const mockToggleMetadataExport = jest.fn().mockResolvedValue(undefined);
let mockMetadataExport = false;

jest.mock('@/api/api-functions', () => ({
  startMetadataExport: () => mockStartMetadataExport(),
  getMetadataExportStatus: () => mockGetMetadataExportStatus(),
}));

jest.mock('@/hooks/useUserPreferences', () => ({
  useUserPreferences: () => ({
    preferences: { Metadata_Export: mockMetadataExport },
    toggleMetadataExport: mockToggleMetadataExport,
  }),
}));

const status = (
  overrides: Partial<MetadataExportStatus> = {},
): MetadataExportStatus => ({
  total: 12,
  pending: 12,
  failed: 0,
  left_alone: 0,
  running: false,
  run_failed: false,
  last_run: null,
  ...overrides,
});

const respond = (data: MetadataExportStatus) => ({
  success: true,
  message: 'ok',
  data,
});

beforeEach(() => {
  jest.clearAllMocks();
  mockMetadataExport = false;
  mockStartMetadataExport.mockResolvedValue(respond(status({ running: true })));
  mockGetMetadataExportStatus.mockResolvedValue(respond(status()));
});

describe('describeExportStatus', () => {
  it('waits for the first answer', () => {
    expect(describeExportStatus(undefined)).toMatch(/Checking/);
  });

  it('says only PNG is supported when there is nothing to export', () => {
    expect(describeExportStatus(status({ total: 0, pending: 0 }))).toMatch(
      /Only PNG files are supported/,
    );
  });

  it('counts down while running', () => {
    expect(describeExportStatus(status({ running: true, pending: 5 }))).toMatch(
      /5 of 12 PNG images left/,
    );
  });

  it('reports an up-to-date library', () => {
    expect(describeExportStatus(status({ pending: 0 }))).toMatch(
      /All 12 PNG images hold up-to-date metadata/,
    );
  });

  it('mentions retries and files left alone', () => {
    const line = describeExportStatus(
      status({ pending: 3, failed: 2, left_alone: 1 }),
    );
    expect(line).toMatch(/3 of 12 PNG images need/);
    expect(line).toMatch(/2 couldn't be written last time and will be retried/);
    expect(line).toMatch(
      /1 were left alone because their existing metadata couldn't be read or came from a newer version of PictoPy/,
    );
  });

  it('reports a crashed run', () => {
    expect(
      describeExportStatus(status({ run_failed: true, pending: 4 })),
    ).toMatch(/stopped with an error\. 4 PNG image/);
  });
});

describe('MetadataExportCard', () => {
  it('reflects the stored preference and toggles it', async () => {
    const user = userEvent.setup();
    mockMetadataExport = true;
    render(<MetadataExportCard />);

    const toggle = screen.getByRole('switch', {
      name: /Save Metadata Automatically/i,
    });
    expect(toggle).toBeChecked();
    await user.click(toggle);
    expect(mockToggleMetadataExport).toHaveBeenCalledTimes(1);
  });

  it('shows where the library stands', async () => {
    render(<MetadataExportCard />);
    expect(
      await screen.findByText(/12 of 12 PNG images need their metadata saved/),
    ).toBeInTheDocument();
  });

  it('starts an export and shows it running', async () => {
    const user = userEvent.setup();
    mockGetMetadataExportStatus
      .mockResolvedValueOnce(respond(status()))
      .mockResolvedValue(respond(status({ running: true, pending: 7 })));
    render(<MetadataExportCard />);

    await user.click(
      await screen.findByRole('button', { name: /Export metadata/i }),
    );
    expect(mockStartMetadataExport).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Exporting/i })).toBeDisabled(),
    );
    expect(screen.getByText(/7 of 12 PNG images left/)).toBeInTheDocument();
  });

  it('runs whether or not automatic export is on', async () => {
    const user = userEvent.setup();
    mockMetadataExport = false;
    render(<MetadataExportCard />);
    await user.click(
      await screen.findByRole('button', { name: /Export metadata/i }),
    );
    expect(mockStartMetadataExport).toHaveBeenCalled();
  });

  it('offers a retry after a crashed run', async () => {
    mockGetMetadataExportStatus.mockResolvedValue(
      respond(status({ run_failed: true, pending: 4 })),
    );
    render(<MetadataExportCard />);
    expect(
      await screen.findByRole('button', { name: /Retry export/i }),
    ).toBeEnabled();
  });

  it('has nothing to export without PNG images', async () => {
    mockGetMetadataExportStatus.mockResolvedValue(
      respond(status({ total: 0, pending: 0 })),
    );
    render(<MetadataExportCard />);
    await screen.findByText(/Only PNG files are supported/);
    expect(
      screen.getByRole('button', { name: /Export metadata/i }),
    ).toBeDisabled();
  });

  it('keeps the button usable when starting fails', async () => {
    const user = userEvent.setup();
    mockStartMetadataExport.mockRejectedValue(new Error('backend down'));
    const consoleError = jest.spyOn(console, 'error').mockImplementation();
    render(<MetadataExportCard />);
    await user.click(
      await screen.findByRole('button', { name: /Export metadata/i }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /Export metadata/i }),
      ).toBeEnabled(),
    );
    consoleError.mockRestore();
  });

  it('tells the user shared links never carry the data', () => {
    render(<MetadataExportCard />);
    expect(
      screen.getByText(/shared by link never include this data/i),
    ).toBeInTheDocument();
  });
});
