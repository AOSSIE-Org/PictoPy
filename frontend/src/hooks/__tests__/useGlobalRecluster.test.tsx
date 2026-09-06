import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useGlobalRecluster } from '@/hooks/useGlobalRecluster';
import {
  startGlobalReclustering,
  getGlobalReclusterStatus,
} from '@/api/api-functions/face_clusters';

jest.mock('@/api/api-functions/face_clusters', () => ({
  startGlobalReclustering: jest.fn(),
  getGlobalReclusterStatus: jest.fn(),
}));

const mockStart = startGlobalReclustering as jest.MockedFunction<
  typeof startGlobalReclustering
>;
const mockStatus = getGlobalReclusterStatus as jest.MockedFunction<
  typeof getGlobalReclusterStatus
>;

const POLL_INTERVAL_MS = 2000;

const startOk = { success: true, message: 'started', data: { task_id: 'abc' } };
const running = {
  success: true,
  data: {
    status: 'running' as const,
    clusters_created: null,
    faces_skipped: null,
  },
};
const complete = {
  success: true,
  message: 'done',
  data: { status: 'complete' as const, clusters_created: 3, faces_skipped: 1 },
};
const errored = {
  success: false,
  message: 'reclustering failed',
  data: {
    status: 'error' as const,
    clusters_created: null,
    faces_skipped: null,
  },
};

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const utils = renderHook(() => useGlobalRecluster(), { wrapper });
  return { ...utils, invalidateSpy };
}

// Flush pending promises and advance fake timers together.
const flush = async (ms = 0) => {
  await act(async () => {
    await Promise.resolve();
    await jest.advanceTimersByTimeAsync(ms);
  });
};

beforeEach(() => {
  jest.useFakeTimers();
  mockStart.mockReset();
  mockStatus.mockReset();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('useGlobalRecluster', () => {
  test('polls until the job completes successfully', async () => {
    mockStart.mockResolvedValue(startOk);
    mockStatus.mockResolvedValueOnce(running).mockResolvedValueOnce(complete);

    const { result, invalidateSpy } = setup();

    act(() => {
      result.current.trigger();
    });
    expect(result.current.isPending).toBe(true);

    await flush(); // start resolves, first poll -> running
    expect(mockStatus).toHaveBeenCalledTimes(1);
    expect(result.current.isPending).toBe(true);

    await flush(POLL_INTERVAL_MS); // scheduled poll -> complete
    expect(result.current.isSuccess).toBe(true);
    expect(result.current.successData).toEqual(complete.data);
    expect(result.current.successMessage).toBe('done');
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['clusters'] });
  });

  test('sets an error when the job reports failure', async () => {
    mockStart.mockResolvedValue(startOk);
    mockStatus.mockResolvedValue(errored);

    const { result, invalidateSpy } = setup();
    act(() => {
      result.current.trigger();
    });
    await flush();

    expect(result.current.isError).toBe(true);
    expect(result.current.errorMessage).toBe('reclustering failed');
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['clusters'] });
  });

  test('sets an error when starting the job fails', async () => {
    mockStart.mockRejectedValue(new Error('network down'));

    const { result } = setup();
    act(() => {
      result.current.trigger();
    });
    await flush();

    expect(result.current.isError).toBe(true);
    expect(mockStatus).not.toHaveBeenCalled();
  });

  test('sets an error when the status request itself rejects (e.g. 404 for an aged-out task)', async () => {
    mockStart.mockResolvedValue(startOk);
    const notFound = {
      isAxiosError: true,
      message: 'Request failed with status code 404',
      code: 'ERR_BAD_REQUEST',
      response: { status: 404, data: {} },
    };
    mockStatus.mockRejectedValue(notFound);

    const { result, invalidateSpy } = setup();
    act(() => {
      result.current.trigger();
    });
    await flush();

    expect(result.current.isError).toBe(true);
    expect(result.current.errorMessage).toBe(
      'ERR_BAD_REQUEST: Request failed with status code 404',
    );
    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  test('stops polling after unmount', async () => {
    mockStart.mockResolvedValue(startOk);
    mockStatus.mockResolvedValue(running);

    const { result, unmount } = setup();
    act(() => {
      result.current.trigger();
    });
    await flush(); // first poll
    expect(mockStatus).toHaveBeenCalledTimes(1);

    unmount();
    await flush(POLL_INTERVAL_MS * 3);
    // No further polls once unmounted.
    expect(mockStatus).toHaveBeenCalledTimes(1);
  });

  test('a rapid second trigger does not leave a second poll loop running', async () => {
    mockStart.mockResolvedValue(startOk);
    mockStatus.mockResolvedValue(running);

    const { result } = setup();
    // Both triggers fire before startGlobalReclustering resolves.
    act(() => {
      result.current.trigger();
      result.current.trigger();
    });

    await flush(); // both starts resolve; only the latest run may poll
    expect(mockStatus).toHaveBeenCalledTimes(1);

    const callsBefore = mockStatus.mock.calls.length;
    await flush(POLL_INTERVAL_MS); // exactly one loop advances
    expect(mockStatus.mock.calls.length).toBe(callsBefore + 1);
  });
});
