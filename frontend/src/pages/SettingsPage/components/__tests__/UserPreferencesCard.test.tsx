import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';

import UserPreferencesCard from '../UserPreferencesCard';
import type { MemoriesPreferences } from '@/api/api-functions/user_preferences';
import type { FaceScanStatus } from '@/api/api-functions/videos';

const mockUpdateMemoriesPreferences = jest.fn().mockResolvedValue(undefined);
const mockToggleVideoFaceDetection = jest.fn().mockResolvedValue(undefined);
const mockStartVideoFaceScan = jest.fn();
const mockGetVideoFaceScanStatus = jest.fn();
let mockVideoFaceDetection = false;
let mockMemories: MemoriesPreferences;
let mockIsUpdating = false;

const scanStatus = (status: FaceScanStatus) => ({
  success: true,
  message: 'ok',
  data: status,
});

jest.mock('@/api/api-functions', () => ({
  purgeVideoFrameCache: jest.fn().mockResolvedValue({ bytes_reclaimed: 0 }),
  startVideoFaceScan: () => mockStartVideoFaceScan(),
  getVideoFaceScanStatus: () => mockGetVideoFaceScanStatus(),
}));

jest.mock('@/hooks/useUserPreferences', () => ({
  useUserPreferences: () => ({
    preferences: {
      YOLO_model_size: 'nano',
      GPU_Acceleration: false,
      Video_Frame_Interval: 5,
      Video_Face_Detection: mockVideoFaceDetection,
      memories: mockMemories,
    },
    memoriesPreferences: mockMemories,
    isLoading: false,
    updateYoloModelSize: jest.fn().mockResolvedValue(undefined),
    toggleGpuAcceleration: jest.fn().mockResolvedValue(undefined),
    updateVideoFrameInterval: jest.fn().mockResolvedValue(undefined),
    toggleVideoFaceDetection: mockToggleVideoFaceDetection,
    updateMemoriesPreferences: mockUpdateMemoriesPreferences,
    refetch: jest.fn().mockResolvedValue(undefined),
    isUpdating: mockIsUpdating,
  }),
}));

const memoriesWith = (
  overrides: Partial<MemoriesPreferences> = {},
): MemoriesPreferences => ({
  enabled: true,
  notifications_enabled: false,
  story_music_enabled: false,
  slide_duration_seconds: 5,
  min_images: 5,
  max_images: 30,
  weights: {
    favourite: 0.22,
    known_people: 0.2,
    event_strength: 0.18,
    face_presence: 0.12,
    semantic_confidence: 0.1,
    gps_novelty: 0.1,
    in_album: 0.08,
  },
  ...overrides,
});

/** Expand the collapsible group; its controls are not mounted until then. */
const openPanel = async (user: ReturnType<typeof userEvent.setup>) => {
  await user.click(
    screen.getByRole('button', { name: /Control how memories are generated/i }),
  );
};

const trigger = (id: string) =>
  document.getElementById(id) as HTMLButtonElement;

const choose = async (
  user: ReturnType<typeof userEvent.setup>,
  id: string,
  option: RegExp,
) => {
  await user.click(trigger(id));
  await user.click(screen.getByRole('menuitem', { name: option }));
};

beforeEach(() => {
  mockUpdateMemoriesPreferences.mockClear();
  mockMemories = memoriesWith();
  mockIsUpdating = false;
  mockVideoFaceDetection = false;
  mockStartVideoFaceScan
    .mockReset()
    .mockResolvedValue(scanStatus({ total: 9, scanned: 0, pending: 9 }));
  mockGetVideoFaceScanStatus
    .mockReset()
    .mockResolvedValue(scanStatus({ total: 9, scanned: 0, pending: 9 }));
});

describe('UserPreferencesCard memories panel', () => {
  it('sends the toggles as patches', async () => {
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await user.click(
      screen.getByRole('switch', { name: /Generate Memories/i }),
    );
    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      enabled: false,
    });
  });

  it('locks notifications behind the generate toggle', async () => {
    mockMemories = memoriesWith({ enabled: false });
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    // Alerting about memories that are never generated is a dead control.
    expect(
      screen.getByRole('switch', { name: /Desktop Notifications/i }),
    ).toBeDisabled();
  });

  it('raises the maximum when a larger minimum is chosen', async () => {
    // Reachable only from values the old sliders allowed; the dropdown
    // options alone cannot put min above max.
    mockMemories = memoriesWith({ min_images: 2, max_images: 5 });
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await choose(user, 'memories-min', /^8 photos$/);

    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      min_images: 8,
      max_images: 8,
    });
  });

  it('lowers the minimum when a smaller maximum is chosen', async () => {
    mockMemories = memoriesWith({ min_images: 40, max_images: 50 });
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await choose(user, 'memories-max', /^20 photos$/);

    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      max_images: 20,
      min_images: 20,
    });
  });

  it('leaves a valid pair alone', async () => {
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await choose(user, 'memories-min', /^3 photos$/);

    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      min_images: 3,
      max_images: 30,
    });
  });

  it('shows a stored value that is not one of the options', async () => {
    mockMemories = memoriesWith({
      slide_duration_seconds: 12,
      min_images: 40,
      max_images: 50,
    });
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    expect(trigger('memories-duration')).toHaveTextContent('12s');
    expect(trigger('memories-min')).toHaveTextContent('40 photos');
    expect(trigger('memories-max')).toHaveTextContent('50 photos');
  });

  it('sends the chosen slide duration', async () => {
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await choose(user, 'memories-duration', /^7 seconds$/);

    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      slide_duration_seconds: 7,
    });
  });

  it('disables every control while a save is pending', async () => {
    mockIsUpdating = true;
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    expect(
      screen.getByRole('switch', { name: /Generate Memories/i }),
    ).toBeDisabled();
    expect(
      screen.getByRole('switch', { name: /Desktop Notifications/i }),
    ).toBeDisabled();
    expect(trigger('memories-duration')).toBeDisabled();
    expect(trigger('memories-min')).toBeDisabled();
    expect(trigger('memories-max')).toBeDisabled();
  });
});

describe('UserPreferencesCard video face detection', () => {
  const openVideoPanel = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(
      screen.getByRole('button', { name: /Control how videos are sampled/i }),
    );
  };

  it('turns finding people in videos on from the video settings', async () => {
    mockVideoFaceDetection = false;
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openVideoPanel(user);

    const toggle = screen.getByRole('switch', {
      name: /Find People in Videos/i,
    });
    expect(toggle).not.toBeChecked();

    await user.click(toggle);
    expect(mockToggleVideoFaceDetection).toHaveBeenCalled();
  });

  it('reflects the stored preference', async () => {
    mockVideoFaceDetection = true;
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openVideoPanel(user);

    expect(
      screen.getByRole('switch', { name: /Find People in Videos/i }),
    ).toBeChecked();
  });

  it('offers to scan existing videos only once the switch is on', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<UserPreferencesCard />);
    await openVideoPanel(user);

    // With the switch off there is nothing the scan could add.
    expect(
      screen.queryByRole('button', { name: /Scan videos/i }),
    ).not.toBeInTheDocument();

    mockVideoFaceDetection = true;
    rerender(<UserPreferencesCard />);

    expect(
      await screen.findByRole('button', { name: /Scan videos/i }),
    ).toBeInTheDocument();
  });

  it('waits to be asked rather than claiming it is already scanning', async () => {
    // Unscanned videos are the normal state before the user asks for a scan,
    // so a backlog on its own must not read as work in progress.
    mockVideoFaceDetection = true;
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openVideoPanel(user);

    expect(
      await screen.findByRole('button', { name: /Scan videos/i }),
    ).toBeEnabled();
    expect(await screen.findByText(/9 video\(s\)/i)).toBeInTheDocument();
  });

  it('starts a scan and reports how far it has got', async () => {
    mockVideoFaceDetection = true;
    mockGetVideoFaceScanStatus
      .mockResolvedValueOnce(scanStatus({ total: 9, scanned: 0, pending: 9 }))
      .mockResolvedValue(scanStatus({ total: 9, scanned: 4, pending: 5 }));
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openVideoPanel(user);

    await user.click(
      await screen.findByRole('button', { name: /Scan videos/i }),
    );

    expect(mockStartVideoFaceScan).toHaveBeenCalled();
    expect(await screen.findByText(/4 of 9 done/i)).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Scanning/i })).toBeDisabled(),
    );
  });

  it('says so when every video has been scanned', async () => {
    mockVideoFaceDetection = true;
    mockGetVideoFaceScanStatus.mockResolvedValue(
      scanStatus({ total: 9, scanned: 9, pending: 0 }),
    );
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openVideoPanel(user);

    expect(
      await screen.findByRole('button', { name: /All scanned/i }),
    ).toBeDisabled();
  });
});
