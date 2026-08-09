import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import {
  usePictoMutation,
  usePictoQuery,
  type BackendRes,
} from '@/hooks/useQueryExtension';
import {
  deleteMemory,
  generateMemories,
  getMemories,
  getMemory,
  getMemoryStatus,
  getTodayMemory,
  patchMemory,
  type ListMemoriesParams,
  type MemoryCard,
  type MemoryStatusData,
  type MemoryStory,
} from '@/api/api-functions/memories';

export const MEMORIES_QUERY_KEY = ['memories'];

/** How often the status endpoint is polled while a run is in flight. */
const RUN_POLL_INTERVAL_MS = 2000;

/**
 * How long to keep watching for a queued run to start.
 *
 * Curation shares one single-worker executor with indexing and semantic
 * scoring, so a run can sit queued for a while - but not indefinitely, and
 * watching forever would poll forever.
 */
const RUN_START_TIMEOUT_MS = 90_000;

// usePictoQuery cannot infer its payload generic from the query function, so
// every hook below pins it explicitly to keep `successData` typed.

/** Memory cards for the grid and filmstrip. */
export const useMemories = (params?: ListMemoriesParams) => {
  type Data = { memories: MemoryCard[]; total_count: number };
  return usePictoQuery<BackendRes<Data>, unknown, Data>({
    queryKey: [...MEMORIES_QUERY_KEY, 'list', params ?? {}],
    queryFn: () => getMemories(params),
    staleTime: 5 * 60 * 1000,
  });
};

/** The memory to surface now; `successData.memory` may be null. */
export const useTodayMemory = () => {
  type Data = { memory: MemoryStory | null };
  return usePictoQuery<BackendRes<Data>, unknown, Data>({
    queryKey: [...MEMORIES_QUERY_KEY, 'today'],
    queryFn: getTodayMemory,
    staleTime: 5 * 60 * 1000,
  });
};

/** A single memory with its images. Skipped when no id is selected. */
export const useMemory = (memoryId?: string) => {
  type Data = { memory: MemoryStory };
  return usePictoQuery<BackendRes<Data>, unknown, Data>({
    queryKey: [...MEMORIES_QUERY_KEY, 'detail', memoryId],
    queryFn: () => getMemory(memoryId as string),
    enabled: Boolean(memoryId),
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Scheduler snapshot. Polled while a run is in progress.
 *
 * `forcePolling` covers the gap before a run is visible: POST /generate
 * returns once the run is queued, which is earlier than the worker process
 * writing 'running', so waiting for that status to appear on its own can
 * mean never polling at all.
 */
export const useMemoryStatus = (
  enabled: boolean = true,
  forcePolling: boolean = false,
) => {
  return usePictoQuery<BackendRes<MemoryStatusData>, unknown, MemoryStatusData>(
    {
      queryKey: [...MEMORIES_QUERY_KEY, 'status'],
      queryFn: getMemoryStatus,
      enabled,
      // Curation runs in a background process, so poll until it settles rather
      // than leaving the page stale.
      refetchInterval: (query) =>
        forcePolling || query.state.data?.data?.run_status === 'running'
          ? RUN_POLL_INTERVAL_MS
          : false,
    },
  );
};

/**
 * POST /generate returns once the run is *queued*, minutes before it runs, so
 * invalidating on the response just refetches what is already on screen -- the
 * reason Refresh used to look like it did nothing. This follows the run
 * instead, refreshing as results land and once more when it settles.
 */
export const useRefreshMemories = () => {
  const queryClient = useQueryClient();
  const [isAwaitingRun, setIsAwaitingRun] = useState(false);
  const requestedAtRef = useRef<number | null>(null);
  // The run that was already on record when Refresh was pressed. Anything
  // with a different start time is the run we asked for.
  const previousRunRef = useRef<string | null | undefined>(undefined);

  const status = useMemoryStatus(true, isAwaitingRun);
  const runStatus = status.successData?.run_status ?? null;
  const runStartedAt = status.successData?.run_started_at ?? null;
  const statusUpdatedAt = status.dataUpdatedAt;
  const isRunActive = isAwaitingRun || runStatus === 'running';

  const mutation = usePictoMutation({
    mutationFn: generateMemories,
    onSuccess: () => {
      requestedAtRef.current = Date.now();
      // Undefined when the first status has not arrived yet, which is not
      // the same as "there was no run" - the fallbacks below cover it.
      previousRunRef.current = status.isSuccess ? runStartedAt : undefined;
      setIsAwaitingRun(true);
    },
  });

  // Only the list key, never the whole tree: invalidating 'status' here
  // would refetch the very query driving this effect, on a 2s loop.
  const wasRunActive = useRef(false);
  useEffect(() => {
    if (isRunActive || wasRunActive.current) {
      void queryClient.invalidateQueries({
        queryKey: [...MEMORIES_QUERY_KEY, 'list'],
      });
    }
    wasRunActive.current = isRunActive;
  }, [isRunActive, statusUpdatedAt, queryClient]);

  // Stop force-polling once our run is on record. Keyed on the start time
  // rather than on seeing 'running': a run over a small library can begin
  // and finish between two polls, and waiting to catch it mid-flight left
  // the button spinning long after the memories had landed.
  useEffect(() => {
    if (!isAwaitingRun) return;

    const baseline = previousRunRef.current;
    const isOurRun = baseline !== undefined && runStartedAt !== baseline;
    const requestedAt = requestedAtRef.current;
    const waitedTooLong =
      requestedAt !== null && Date.now() - requestedAt > RUN_START_TIMEOUT_MS;

    if (isOurRun || runStatus === 'running' || waitedTooLong) {
      setIsAwaitingRun(false);
    }
  }, [isAwaitingRun, runStartedAt, runStatus, statusUpdatedAt]);

  const refresh = useCallback(
    (force: boolean = true) => mutation.mutate({ force }),
    [mutation],
  );

  return {
    refresh,
    /** True from the click until the run has finished, not just until it is queued. */
    isRefreshing: mutation.isPending || isRunActive,
    status,
  };
};

export const useUpdateMemory = () => {
  return usePictoMutation({
    mutationFn: patchMemory,
    autoInvalidateTags: MEMORIES_QUERY_KEY,
  });
};

export const useDeleteMemory = () => {
  return usePictoMutation({
    mutationFn: deleteMemory,
    autoInvalidateTags: MEMORIES_QUERY_KEY,
  });
};
