import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';

import UserPreferencesCard from '../UserPreferencesCard';
import type { MemoriesPreferences } from '@/api/api-functions/user_preferences';
import {
  isPermissionGranted,
  requestPermission,
} from '@tauri-apps/plugin-notification';

const mockIsPermissionGranted = jest.mocked(isPermissionGranted);
const mockRequestPermission = jest.mocked(requestPermission);

const mockUpdateMemoriesPreferences = jest.fn().mockResolvedValue(undefined);
let mockMemories: MemoriesPreferences;
let mockIsUpdating = false;

jest.mock('@/hooks/useUserPreferences', () => ({
  useUserPreferences: () => ({
    preferences: {
      YOLO_model_size: 'nano',
      GPU_Acceleration: false,
      Video_Frame_Interval: 5,
      memories: mockMemories,
    },
    memoriesPreferences: mockMemories,
    isLoading: false,
    updateYoloModelSize: jest.fn().mockResolvedValue(undefined),
    toggleGpuAcceleration: jest.fn().mockResolvedValue(undefined),
    updateVideoFrameInterval: jest.fn().mockResolvedValue(undefined),
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
  mockIsPermissionGranted.mockReset().mockResolvedValue(true);
  mockRequestPermission.mockReset().mockResolvedValue('granted');
  mockMemories = memoriesWith();
  mockIsUpdating = false;
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

  it('asks the OS for permission when notifications are turned on', async () => {
    mockIsPermissionGranted.mockResolvedValue(false);
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await user.click(
      screen.getByRole('switch', { name: /Desktop Notifications/i }),
    );

    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      notifications_enabled: true,
    });
    expect(mockRequestPermission).toHaveBeenCalled();
  });

  it('does not ask again once permission is held', async () => {
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await user.click(
      screen.getByRole('switch', { name: /Desktop Notifications/i }),
    );

    expect(mockIsPermissionGranted).toHaveBeenCalled();
    expect(mockRequestPermission).not.toHaveBeenCalled();
  });

  it('turns notifications off without touching the OS', async () => {
    mockMemories = memoriesWith({ notifications_enabled: true });
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await user.click(
      screen.getByRole('switch', { name: /Desktop Notifications/i }),
    );

    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      notifications_enabled: false,
    });
    expect(mockIsPermissionGranted).not.toHaveBeenCalled();
  });

  // A refused or unavailable prompt is the OS having the last word, not a
  // reason to lose the preference the user just set.
  it('keeps the preference when the permission call fails', async () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    mockIsPermissionGranted.mockRejectedValue(new Error('unavailable'));
    const user = userEvent.setup();
    render(<UserPreferencesCard />);
    await openPanel(user);

    await user.click(
      screen.getByRole('switch', { name: /Desktop Notifications/i }),
    );

    expect(mockUpdateMemoriesPreferences).toHaveBeenCalledWith({
      notifications_enabled: true,
    });
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
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
