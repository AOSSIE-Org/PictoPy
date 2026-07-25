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
  totalImages: number;
  taggedImages: number;
  embeddedImages: number;
}

const aggregate = (data: APIResponse | undefined) => {
  const rawFolders = data?.data;
  const folders = Array.isArray(rawFolders)
    ? (rawFolders as FolderTaggingInfo[])
    : [];

  let totalImages = 0;
  let taggedImages = 0;
  let embeddedImages = 0;
  for (const folder of folders) {
    // Only AI-tagging folders are ever processed
    if (!folder?.ai_tagging) continue;
    totalImages += folder.total_images ?? 0;
    taggedImages += folder.tagged_images ?? 0;
    embeddedImages += folder.embedded_images ?? 0;
  }
  return { totalImages, taggedImages, embeddedImages };
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
      const { totalImages, taggedImages, embeddedImages } = aggregate(
        query.state.data,
      );
      const busy =
        taggedImages < totalImages ||
        (semanticAvailable && embeddedImages < totalImages);
      return busy ? 1000 : 10000;
    },
    refetchIntervalInBackground: true,
    retry: 2,
    retryOnMount: false,
    refetchOnWindowFocus: false,
  });

  const { totalImages, taggedImages, embeddedImages } = aggregate(
    taggingStatusQuery.data,
  );

  let phase: LibraryProcessingPhase = 'idle';
  let percentage = 100;
  if (totalImages > 0 && taggedImages < totalImages) {
    phase = 'tagging';
    percentage = (taggedImages / totalImages) * 100;
  } else if (
    semanticAvailable &&
    totalImages > 0 &&
    embeddedImages < totalImages
  ) {
    phase = 'indexing';
    percentage = (embeddedImages / totalImages) * 100;
  }

  return {
    semanticAvailable,
    phase,
    percentage,
    totalImages,
    taggedImages,
    embeddedImages,
  };
};
