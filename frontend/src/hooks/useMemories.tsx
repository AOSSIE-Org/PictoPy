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

/** Scheduler snapshot. Polled while a run is in progress. */
export const useMemoryStatus = (enabled: boolean = true) => {
  return usePictoQuery<BackendRes<MemoryStatusData>, unknown, MemoryStatusData>(
    {
      queryKey: [...MEMORIES_QUERY_KEY, 'status'],
      queryFn: getMemoryStatus,
      enabled,
      // Curation runs in a background process, so poll until it settles rather
      // than leaving the page stale.
      refetchInterval: (query) =>
        query.state.data?.data?.run_status === 'running' ? 3000 : false,
    },
  );
};

export const useGenerateMemories = () => {
  return usePictoMutation({
    mutationFn: generateMemories,
    autoInvalidateTags: MEMORIES_QUERY_KEY,
  });
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
