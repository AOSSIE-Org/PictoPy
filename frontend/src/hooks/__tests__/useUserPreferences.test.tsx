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

// A response reaches the cache a tick before the effect that applies it, so
// asserting on resolve reads state nothing has overwritten yet.
const settle = async () => {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
};

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

/** Mirrors the route's _deep_merge, so a patch behaves as the server does. */
const deepMerge = <T extends object>(base: T, updates: object): T => {
  const merged = { ...base } as Record<string, unknown>;
  for (const [key, value] of Object.entries(updates)) {
    const existing = merged[key];
    merged[key] =
      isPlainObject(value) && isPlainObject(existing)
        ? deepMerge(existing, value)
        : value;
  }
  return merged as T;
};

/** Stands in for the stored blob so reads and writes agree. */
let stored: UserPreferencesData;
const payload = (user_preferences: UserPreferencesData) => ({
  success: true,
  message: 'ok',
  user_preferences,
});

beforeEach(() => {
  stored = JSON.parse(JSON.stringify(baseline));

  mockGetUserPreferences
    .mockReset()
    .mockImplementation(async () => payload(stored));

  mockUpdateUserPreferences
    .mockReset()
    .mockImplementation(async (request: UpdateUserPreferencesRequest) => {
      stored = deepMerge(stored, request);
      return payload(stored);
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
        stored = deepMerge(stored, request);
        return payload(stored);
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

  it('ignores a load that lands while a write is pending', async () => {
    const result = await mountLoaded();

    // A read already in flight when the write starts. It carries someone
    // else's change, so react-query does not dedupe it, and the pre-write
    // value for the key the write is about to change.
    mockGetUserPreferences.mockResolvedValue(
      payload({
        ...JSON.parse(JSON.stringify(baseline)),
        YOLO_model_size: 'small',
        Video_Frame_Interval: 5,
      }),
    );

    let release = () => {};
    mockUpdateUserPreferences.mockImplementationOnce(
      async (request: UpdateUserPreferencesRequest) => {
        await new Promise<void>((resolve) => {
          release = resolve;
        });
        stored = deepMerge(stored, request);
        return payload(stored);
      },
    );

    let write: Promise<unknown> = Promise.resolve();
    await act(async () => {
      write = result.current.updateVideoFrameInterval(30);
      await result.current.refetch();
    });

    // Applying the load here would revert the optimistic value and hand the
    // next queued write a stale base.
    expect(result.current.preferences.Video_Frame_Interval).toBe(30);

    await act(async () => {
      release();
      await write;
    });
    await settle();

    expect(result.current.preferences.Video_Frame_Interval).toBe(30);
  });

  it('ignores a load that started before a write but lands after it', async () => {
    const result = await mountLoaded();

    // Held open until the write has fully settled, so the pending-write guard
    // is back to zero by the time the response arrives.
    let releaseRead = () => {};
    mockGetUserPreferences.mockImplementationOnce(async () => {
      await new Promise<void>((resolve) => {
        releaseRead = resolve;
      });
      return payload({
        ...JSON.parse(JSON.stringify(baseline)),
        YOLO_model_size: 'small',
        Video_Frame_Interval: 5,
      });
    });

    let read: Promise<unknown> = Promise.resolve();
    await act(async () => {
      read = result.current.refetch();
      await Promise.resolve();
    });

    await act(async () => {
      await result.current.updateVideoFrameInterval(30);
    });
    expect(result.current.preferences.Video_Frame_Interval).toBe(30);

    await act(async () => {
      releaseRead();
      await read;
    });
    await settle();

    // A read that starts first can still finish last, so arrival order alone
    // cannot tell this response apart from a current one.
    expect(result.current.preferences.Video_Frame_Interval).toBe(30);
    expect(result.current.preferences.YOLO_model_size).toBe('medium');
  });

  it('adopts the merged result the server returns', async () => {
    const result = await mountLoaded();

    // The server normalizes weights on read, so the response is the truth
    // rather than what was optimistically applied.
    mockUpdateUserPreferences.mockImplementationOnce(async () =>
      payload(deepMerge(stored, { Video_Frame_Interval: 2 })),
    );

    await act(async () => {
      await result.current.updateVideoFrameInterval(30);
    });

    expect(result.current.preferences.Video_Frame_Interval).toBe(2);
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
