import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchModelStatus } from '@/api/api-functions';
import { getFoldersTaggingStatus } from '@/api/api-functions/folders';
import { isSemanticSearchAvailable } from '@/types/models';
import { FolderTaggingInfo } from '@/types/FolderStatus';
import { APIResponse } from '@/types/API';

/** Current background pass, in backend pipeline order: tagging → indexing. */
export type LibraryProcessingPhase = 'tagging' | 'indexing' | 'idle';

export interface LibraryProcessingStatus {
  /** Semantic Search models are installed and usable */
  semanticAvailable: boolean;
  phase: LibraryProcessingPhase;
  /** Progress (0-100) of the current phase; 100 when idle */
  percentage: number;
  /** Counts are over images and videos combined. */
  totalItems: number;
  taggedItems: number;
  embeddedItems: number;
}

const aggregate = (data: APIResponse | undefined) => {
  const rawFolders = data?.data;
  const folders = Array.isArray(rawFolders)
    ? (rawFolders as FolderTaggingInfo[])
    : [];

  let totalItems = 0;
  let taggedItems = 0;
  let embeddedItems = 0;
  for (const folder of folders) {
    // Only AI-tagging folders are ever processed
    if (!folder?.ai_tagging) continue;
    totalItems += (folder.total_images ?? 0) + (folder.total_videos ?? 0);
    taggedItems += (folder.tagged_images ?? 0) + (folder.tagged_videos ?? 0);
    embeddedItems +=
      (folder.embedded_images ?? 0) + (folder.embedded_videos ?? 0);
  }
  return { totalItems, taggedItems, embeddedItems };
};

/**
 * Aggregated background-processing progress across all AI-tagging folders.
 * Derived purely from polled database state (not task events), so it
 * survives restarts and refreshes. Polls fast while busy, slow when idle.
 */
export const useLibraryProcessingStatus = (): LibraryProcessingStatus => {
  const { data: statusData, isSuccess: isStatusSuccess } = usePictoQuery({
    queryKey: ['models', 'status'],
    queryFn: fetchModelStatus,
  });

  const semanticAvailable =
    isStatusSuccess && statusData?.data
      ? isSemanticSearchAvailable(statusData.data)
      : false;

  const taggingStatusQuery = usePictoQuery({
    queryKey: ['folders', 'tagging-status'],
    queryFn: getFoldersTaggingStatus,
    staleTime: 1000,
    refetchInterval: (query) => {
      const { totalItems, taggedItems, embeddedItems } = aggregate(
        query.state.data,
      );
      const busy =
        taggedItems < totalItems ||
        (semanticAvailable && embeddedItems < totalItems);
      return busy ? 1000 : 10000;
    },
    refetchIntervalInBackground: true,
    retry: 2,
    retryOnMount: false,
    refetchOnWindowFocus: false,
  });

  const { totalItems, taggedItems, embeddedItems } = aggregate(
    taggingStatusQuery.data,
  );

  let phase: LibraryProcessingPhase = 'idle';
  let percentage = 100;
  if (totalItems > 0 && taggedItems < totalItems) {
    phase = 'tagging';
    percentage = (taggedItems / totalItems) * 100;
  } else if (
    semanticAvailable &&
    totalItems > 0 &&
    embeddedItems < totalItems
  ) {
    phase = 'indexing';
    percentage = (embeddedItems / totalItems) * 100;
  }

  return {
    semanticAvailable,
    phase,
    percentage,
    totalItems,
    taggedItems,
    embeddedItems,
  };
};
