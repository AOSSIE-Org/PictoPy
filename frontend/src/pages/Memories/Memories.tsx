import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { MemoryCard } from '@/components/Memories/MemoryCard';
import { ConvertMemoryToAlbumDialog } from '@/components/Memories/ConvertMemoryToAlbumDialog';
import { MemoryStoryViewer } from '@/components/Memories/MemoryStoryViewer';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { useUserPreferences } from '@/hooks/useUserPreferences';
import { useMemories, useRefreshMemories } from '@/hooks/useMemories';
import type { MemoryCard as MemoryCardType } from '@/api/api-functions/memories';
import {
  openMemory,
  selectActiveMemoryId,
  setSlideDuration,
} from '@/features/memoriesSlice';

const MemoryCardSkeleton: React.FC = () => (
  <div className="bg-muted aspect-4/5 w-full animate-pulse rounded-xl" />
);

const EmptyState: React.FC<{ isGenerating: boolean }> = ({ isGenerating }) => (
  <div className="border-border bg-muted/40 rounded-xl border-2 border-dashed p-12 text-center">
    <h2 className="text-lg font-medium">No memories yet</h2>
    <p className="text-muted-foreground mx-auto mt-2 max-w-md text-sm">
      {isGenerating
        ? 'Looking through your library for moments worth revisiting…'
        : 'Add photos with capture dates and enable AI tagging. Memories are curated automatically as your library grows.'}
    </p>
  </div>
);

export const Memories: React.FC = () => {
  const dispatch = useAppDispatch();
  const activeMemoryId = useAppSelector(selectActiveMemoryId);

  const [memoryToConvert, setMemoryToConvert] = useState<MemoryCardType | null>(
    null,
  );

  const memoriesQuery = useMemories({ limit: 60 });
  const { refresh, isRefreshing, status: statusQuery } = useRefreshMemories();
  const { memoriesPreferences } = useUserPreferences();

  const memories = memoriesQuery.successData?.memories ?? [];
  const status = statusQuery.successData;
  const isGenerating = isRefreshing;

  // The slide interval is a user preference; mirror it into the slice the
  // viewer reads from.
  useEffect(() => {
    dispatch(
      setSlideDuration(memoriesPreferences.slide_duration_seconds * 1000),
    );
  }, [dispatch, memoriesPreferences.slide_duration_seconds]);

  useEffect(() => {
    if (!memoriesQuery.isError) return;
    dispatch(
      showInfoDialog({
        title: 'Error Loading Memories',
        message: memoriesQuery.errorMessage || 'Failed to load memories',
        variant: 'error',
      }),
    );
  }, [memoriesQuery.isError, memoriesQuery.errorMessage, dispatch]);

  const handleGenerate = () => {
    // Curating mid-index would score a half-written library, so the backend
    // refuses; say so rather than firing a request that quietly does nothing.
    if (status?.indexing_busy) {
      dispatch(
        showInfoDialog({
          title: 'Indexing in progress',
          message:
            'Your library is still being processed. Memories will be generated once it finishes.',
          variant: 'info',
        }),
      );
      return;
    }
    refresh();
  };

  return (
    <div className="flex h-full flex-col">
      <div className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Memories</h1>
            {status && status.unviewed_count > 0 && (
              <p className="text-muted-foreground mt-1 text-sm">
                {status.unviewed_count} new to look back on
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`}
              />
              {isGenerating ? 'Generating…' : 'Regenerate'}
            </Button>
          </div>
        </div>

        {memoriesQuery.isLoading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 10 }).map((_, index) => (
              <MemoryCardSkeleton key={index} />
            ))}
          </div>
        ) : memories.length === 0 ? (
          <EmptyState isGenerating={Boolean(isGenerating)} />
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {memories.map((memory) => (
              <MemoryCard
                key={memory.memory_id}
                memory={memory}
                onOpen={(id) => dispatch(openMemory(id))}
                onConvertToAlbum={() => setMemoryToConvert(memory)}
              />
            ))}
          </div>
        )}
      </div>

      <ConvertMemoryToAlbumDialog
        memory={memoryToConvert}
        isOpen={memoryToConvert !== null}
        onClose={() => setMemoryToConvert(null)}
      />

      {activeMemoryId && (
        <MemoryStoryViewer
          memoryId={activeMemoryId}
          memories={memories}
          musicEnabled={memoriesPreferences.story_music_enabled}
        />
      )}
    </div>
  );
};

export default Memories;
