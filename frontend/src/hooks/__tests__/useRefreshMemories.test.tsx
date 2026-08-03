import { renderHook, act, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useRefreshMemories, MEMORIES_QUERY_KEY } from '@/hooks/useMemories';

const mockGenerateMemories = jest.fn();
const mockGetMemoryStatus = jest.fn();

jest.mock('@/api/api-functions/memories', () => ({
  generateMemories: (...args: unknown[]) => mockGenerateMemories(...args),
  getMemoryStatus: () => mockGetMemoryStatus(),
  getMemories: jest.fn(),
  getMemory: jest.fn(),
  getTodayMemory: jest.fn(),
  patchMemory: jest.fn(),
  deleteMemory: jest.fn(),
}));

const statusOf = (
  run_status: string | null,
  run_started_at = '2026-07-29T09:00:00',
) => ({
  success: true,
  data: {
    run_date: '2026-07-29',
    run_status,
    run_started_at,
    indexing_busy: false,
    unviewed_count: 0,
    latest_memory_id: null,
    memories_enabled: true,
    notifications_enabled: true,
  },
});

let queryClient: QueryClient;

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const listQueryKey = [...MEMORIES_QUERY_KEY, 'list', {}];

/** Seed the grid query so invalidation is observable. */
const seedList = () =>
  queryClient.setQueryData(listQueryKey, {
    success: true,
    data: { memories: [], total_count: 0 },
  });

const listIsStale = () =>
  queryClient.getQueryState(listQueryKey)?.isInvalidated === true;

beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  mockGenerateMemories
    .mockReset()
    .mockResolvedValue({ success: true, data: {} });
  mockGetMemoryStatus.mockReset().mockResolvedValue(statusOf('complete'));
});

/** A run that started after the one already on record when Refresh ran. */
const RUN_TWO = '2026-07-29T11:30:00';

describe('useRefreshMemories', () => {
  it('stays busy after the request is accepted', async () => {
    // POST /generate returns once the run is queued. Reporting "done" there
    // is what made Refresh look like it had finished before it started.
    const { result } = renderHook(() => useRefreshMemories(), { wrapper });
    await waitFor(() =>
      expect(result.current.status.successData).toBeDefined(),
    );

    await act(async () => {
      result.current.refresh();
    });

    await waitFor(() => expect(result.current.isRefreshing).toBe(true));
  });

  it('refreshes the grid once the run finishes', async () => {
    const { result } = renderHook(() => useRefreshMemories(), { wrapper });
    await waitFor(() =>
      expect(result.current.status.successData).toBeDefined(),
    );
    seedList();

    await act(async () => {
      result.current.refresh();
    });
    mockGetMemoryStatus.mockResolvedValue(statusOf('running', RUN_TWO));
    await waitFor(() => expect(result.current.isRefreshing).toBe(true));

    mockGetMemoryStatus.mockResolvedValue(statusOf('complete', RUN_TWO));

    await waitFor(() => expect(listIsStale()).toBe(true), { timeout: 6000 });
  });

  it('stops reporting busy when the run settles', async () => {
    const { result } = renderHook(() => useRefreshMemories(), { wrapper });
    await waitFor(() =>
      expect(result.current.status.successData).toBeDefined(),
    );

    await act(async () => {
      result.current.refresh();
    });
    mockGetMemoryStatus.mockResolvedValue(statusOf('running', RUN_TWO));
    await waitFor(() => expect(result.current.isRefreshing).toBe(true));

    mockGetMemoryStatus.mockResolvedValue(statusOf('failed', RUN_TWO));

    await waitFor(() => expect(result.current.isRefreshing).toBe(false), {
      timeout: 6000,
    });
  });

  it('does not poll before anything has been asked for', async () => {
    renderHook(() => useRefreshMemories(), { wrapper });

    await waitFor(() => expect(mockGetMemoryStatus).toHaveBeenCalled());
    const callsAfterMount = mockGetMemoryStatus.mock.calls.length;

    await new Promise((resolve) => setTimeout(resolve, 2500));

    // An idle page should sit still rather than poll a settled scheduler.
    expect(mockGetMemoryStatus.mock.calls.length).toBe(callsAfterMount);
  });

  it('stops reporting busy for a run that begins and ends between polls', async () => {
    // A small library curates in under a poll interval. Waiting to catch the
    // run mid-flight left the button spinning long after it had finished.
    const { result } = renderHook(() => useRefreshMemories(), { wrapper });
    await waitFor(() =>
      expect(result.current.status.successData).toBeDefined(),
    );

    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => expect(result.current.isRefreshing).toBe(true));

    mockGetMemoryStatus.mockResolvedValue(statusOf('complete', RUN_TWO));

    await waitFor(() => expect(result.current.isRefreshing).toBe(false), {
      timeout: 6000,
    });
  });

  it('forwards the force flag', async () => {
    const { result } = renderHook(() => useRefreshMemories(), { wrapper });
    await waitFor(() =>
      expect(result.current.status.successData).toBeDefined(),
    );

    await act(async () => {
      result.current.refresh();
    });

    // react-query passes a context object as a second argument.
    expect(mockGenerateMemories.mock.calls[0][0]).toEqual({ force: true });
  });
});
