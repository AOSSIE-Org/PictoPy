import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { rootReducer } from '@/app/store';
import { useUserPreferences } from '@/hooks/useUserPreferences';
import type {
  UpdateUserPreferencesRequest,
  UserPreferencesData,
} from '@/api/api-functions/user_preferences';

const mockGetUserPreferences = jest.fn();
const mockUpdateUserPreferences = jest.fn();

jest.mock('@/api/api-functions/user_preferences', () => ({
  getUserPreferences: () => mockGetUserPreferences(),
  updateUserPreferences: (request: UpdateUserPreferencesRequest) =>
    mockUpdateUserPreferences(request),
}));

const baseline: UserPreferencesData = {
  // Differs from the hook's initial state, so mountLoaded can tell the two
  // apart and does not race the load.
  YOLO_model_size: 'medium',
  GPU_Acceleration: false,
  Video_Frame_Interval: 5,
  memories: {
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
  },
};

/** Built once per test: a client rebuilt on every render remounts the query. */
const makeWrapper = () => {
  const store = configureStore({ reducer: rootReducer });
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </Provider>
  );
};

/** Mount and wait for the initial load to land in local state. */
const mountLoaded = async () => {
  const { result } = renderHook(() => useUserPreferences(), {
    wrapper: makeWrapper(),
  });
  await waitFor(() =>
    expect(result.current.preferences.YOLO_model_size).toBe('medium'),
  );
  return result;
};

const sentBodies = () =>
  mockUpdateUserPreferences.mock.calls.map(([body]) => body);

beforeEach(() => {
  mockGetUserPreferences
    .mockReset()
    // The refetch after a successful write would otherwise overwrite local
    // state from the server and mask what optimistic apply and rollback did.
    .mockResolvedValueOnce({
      success: true,
      message: 'ok',
      user_preferences: baseline,
    })
    .mockImplementation(() => new Promise(() => {}));

  mockUpdateUserPreferences.mockReset().mockResolvedValue({
    success: true,
    message: 'ok',
    user_preferences: baseline,
  });
});

describe('useUserPreferences', () => {
  it('sends only the keys it changed', async () => {
    const result = await mountLoaded();

    await act(async () => {
      await result.current.updateVideoFrameInterval(10);
    });

    // A whole-object PUT would carry a concurrent edit's stale value along
    // with it, so each write names only its own key.
    expect(sentBodies()).toEqual([{ Video_Frame_Interval: 10 }]);
  });

  it('builds a queued write from what landed before it', async () => {
    const result = await mountLoaded();

    // Two toggles from the same render. Reading the render's snapshot rather
    // than the applied value makes both compute the same "next" state.
    await act(async () => {
      const first = result.current.toggleGpuAcceleration();
      const second = result.current.toggleGpuAcceleration();
      await Promise.all([first, second]);
    });

    expect(sentBodies()).toEqual([
      { GPU_Acceleration: true },
      { GPU_Acceleration: false },
    ]);
    expect(result.current.preferences.GPU_Acceleration).toBe(false);
  });

  it('rolls back only the write that failed', async () => {
    mockUpdateUserPreferences.mockImplementation(
      async (request: UpdateUserPreferencesRequest) => {
        if (request.Video_Frame_Interval !== undefined) {
          throw new Error('save failed');
        }
        return { success: true, message: 'ok', user_preferences: baseline };
      },
    );

    const result = await mountLoaded();

    await act(async () => {
      const memories = result.current.updateMemoriesPreferences({
        min_images: 8,
      });
      const interval = result.current
        .updateVideoFrameInterval(30)
        .catch(() => undefined);
      await Promise.all([memories, interval]);
    });

    // The failed write must restore its own key and leave the successful one
    // alone. A snapshot captured before the memories write applied would
    // revert min_images to 5 here.
    await waitFor(() =>
      expect(result.current.preferences.Video_Frame_Interval).toBe(5),
    );
    expect(result.current.memoriesPreferences.min_images).toBe(8);
  });

  it('keeps accepting writes after one fails', async () => {
    mockUpdateUserPreferences.mockRejectedValueOnce(new Error('save failed'));

    const result = await mountLoaded();

    await act(async () => {
      await result.current.updateVideoFrameInterval(30).catch(() => undefined);
    });

    await act(async () => {
      await result.current.updateVideoFrameInterval(10);
    });

    // A rejection left unhandled in the queue would stall every later write.
    expect(result.current.preferences.Video_Frame_Interval).toBe(10);
  });

  it('merges a memories patch over the stored weights', async () => {
    const result = await mountLoaded();

    await act(async () => {
      await result.current.updateMemoriesPreferences({
        weights: { favourite: 0.5 },
      });
    });

    expect(result.current.memoriesPreferences.weights).toEqual({
      ...baseline.memories.weights,
      favourite: 0.5,
    });
    expect(sentBodies()).toEqual([
      { memories: { weights: { favourite: 0.5 } } },
    ]);
  });
});
