import { memoriesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import type { BackendRes } from '@/hooks/useQueryExtension';

// Data Types

export type MemoryEventType = 'anniversary' | 'import_event' | 'semantic_event';

export type MemoryStatus = 'pending' | 'complete' | 'failed' | 'empty';

export type MemoryRunStatus = 'running' | 'complete' | 'failed';

/** A single curated image within a memory. */
export interface MemoryImage {
  id: string;
  path: string;
  thumbnailPath: string | null;
  captured_at: string | null;
  latitude: number | null;
  longitude: number | null;
  isFavourite: boolean;
  sort_order: number;
  score: number | null;
}

/** Memory summary, without the image set. Backs the grid and filmstrip. */
export interface MemoryCard {
  memory_id: string;
  dedupe_key: string;
  event_type: MemoryEventType;
  status: MemoryStatus;
  title: string;
  subtitle: string | null;
  place_label: string | null;
  center_lat: number | null;
  center_lon: number | null;
  surface_date: string;
  period_start: string | null;
  period_end: string | null;
  image_count: number;
  cover_image_id: string | null;
  cover_thumbnail_path: string | null;
  score: number;
  notified_at: string | null;
  viewed_at: string | null;
  dismissed: boolean;
  created_at: string | null;
}

/** A memory with its full image set, for the story viewer. */
export interface MemoryStory extends MemoryCard {
  images: MemoryImage[];
  signals: Record<string, number> | null;
}

export interface MemoryStatusData {
  run_date: string;
  run_status: MemoryRunStatus | null;
  indexing_busy: boolean;
  unviewed_count: number;
  latest_memory_id: string | null;
  memories_enabled: boolean;
  notifications_enabled: boolean;
}

export interface GenerateMemoriesRequest {
  force?: boolean;
  reference_date?: string;
}

export interface ListMemoriesParams {
  limit?: number;
  offset?: number;
  event_type?: MemoryEventType;
  include_viewed?: boolean;
  include_dismissed?: boolean;
}

export interface UpdateMemoryRequest {
  viewed?: boolean;
  dismissed?: boolean;
  notified?: boolean;
}

// API Functions

/** List memory cards, newest first. */
export const getMemories = async (
  params?: ListMemoriesParams,
): Promise<BackendRes<{ memories: MemoryCard[]; total_count: number }>> => {
  const response = await apiClient.get(memoriesEndpoints.list, { params });
  return response.data;
};

/** Get the memory to surface now. `data.memory` is null when there is none. */
export const getTodayMemory = async (): Promise<
  BackendRes<{ memory: MemoryStory | null }>
> => {
  const response = await apiClient.get(memoriesEndpoints.today);
  return response.data;
};

/** Get a single memory with its full image set. */
export const getMemory = async (
  memoryId: string,
): Promise<BackendRes<{ memory: MemoryStory }>> => {
  const response = await apiClient.get(memoriesEndpoints.byId(memoryId));
  return response.data;
};

/** Queue a curation run. */
export const generateMemories = async (
  request: GenerateMemoriesRequest = {},
): Promise<
  BackendRes<{ run_date: string; status: MemoryRunStatus; queued: boolean }>
> => {
  const response = await apiClient.post(memoriesEndpoints.generate, request);
  return response.data;
};

/** Get the scheduler snapshot. */
export const getMemoryStatus = async (): Promise<
  BackendRes<MemoryStatusData>
> => {
  const response = await apiClient.get(memoriesEndpoints.status);
  return response.data;
};

/** Update a memory's viewed, dismissed or notified state. */
export const patchMemory = async ({
  memoryId,
  ...request
}: UpdateMemoryRequest & {
  memoryId: string;
}): Promise<BackendRes<{ memory: MemoryStory }>> => {
  const response = await apiClient.patch(
    memoriesEndpoints.byId(memoryId),
    request,
  );
  return response.data;
};

/** Delete a memory. The underlying photos are untouched. */
export const deleteMemory = async (
  memoryId: string,
): Promise<BackendRes<{ memory_id: string }>> => {
  const response = await apiClient.delete(memoriesEndpoints.byId(memoryId));
  return response.data;
};
