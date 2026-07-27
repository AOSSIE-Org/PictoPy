import React, { useCallback, useEffect, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Pause,
  Play,
  Settings,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';
import { useNavigate } from 'react-router';

import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { useStoryProgress } from '@/hooks/useStoryProgress';
import { useMemory, useUpdateMemory } from '@/hooks/useMemories';
import { createImageErrorHandler } from '@/utils/imageFallback';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/constants/routes';
import type { MemoryCard } from '@/api/api-functions/memories';
import {
  closeMemory,
  openMemory,
  selectIsMuted,
  selectIsPlaying,
  selectSlideDurationMs,
  selectSlideIndex,
  setPlaying,
  setSlideIndex,
  toggleMuted,
  togglePlaying,
} from '@/features/memoriesSlice';
import {
  MEMORY_PLACEHOLDER_IMAGE,
  formatMemoryDate,
  formatMemorySubtitle,
  getMemoryImageUrl,
} from '@/utils/memories';
import { MemoryFilmstrip } from './MemoryFilmstrip';

const handleImageError = createImageErrorHandler(MEMORY_PLACEHOLDER_IMAGE);

/** Bundled background track. Playback is opt-in via memories preferences. */
const STORY_AUDIO_SRC = '/memory-theme.mp3';

/** Horizontal travel, in px, that counts as a swipe rather than a tap. */
const SWIPE_THRESHOLD = 50;

interface MemoryStoryViewerProps {
  memoryId: string;
  /** Past memories for the filmstrip. */
  memories: MemoryCard[];
  musicEnabled: boolean;
}

/**
 * Full-screen, Instagram-style viewer: segmented progress bars, autoplay,
 * keyboard and swipe navigation, and a filmstrip of other memories.
 */
export const MemoryStoryViewer: React.FC<MemoryStoryViewerProps> = ({
  memoryId,
  memories,
  musicEnabled,
}) => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const slideIndex = useAppSelector(selectSlideIndex);
  const isPlaying = useAppSelector(selectIsPlaying);
  const isMuted = useAppSelector(selectIsMuted);
  const slideDurationMs = useAppSelector(selectSlideDurationMs);

  const { successData, isLoading, isError } = useMemory(memoryId);
  const { mutate: updateMemory } = useUpdateMemory();

  const memory = successData?.memory;
  const images = memory?.images ?? [];
  const total = images.length;
  const safeIndex = Math.min(slideIndex, Math.max(total - 1, 0));
  const currentImage = images[safeIndex];

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const markedViewedRef = useRef<string | null>(null);

  const handleClose = useCallback(() => {
    dispatch(closeMemory());
  }, [dispatch]);

  const goTo = useCallback(
    (index: number) => {
      if (index < 0) return;
      if (index >= total) {
        // Reaching the end closes the story rather than looping, so the user
        // lands back in the grid instead of being stuck in a cycle.
        handleClose();
        return;
      }
      dispatch(setSlideIndex(index));
    },
    [dispatch, handleClose, total],
  );

  const goNext = useCallback(() => goTo(safeIndex + 1), [goTo, safeIndex]);
  const goPrevious = useCallback(
    () => goTo(Math.max(safeIndex - 1, 0)),
    [goTo, safeIndex],
  );

  const progress = useStoryProgress({
    index: safeIndex,
    durationMs: slideDurationMs,
    isPlaying: isPlaying && total > 0,
    onComplete: goNext,
  });

  // Opening a memory clears its unread state. Guarded by id so a re-render or
  // a refetch does not fire the mutation repeatedly.
  useEffect(() => {
    if (!memory || memory.viewed_at !== null) return;
    if (markedViewedRef.current === memory.memory_id) return;
    markedViewedRef.current = memory.memory_id;
    updateMemory({ memoryId: memory.memory_id, viewed: true });
  }, [memory, updateMemory]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowRight':
          event.preventDefault();
          goNext();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          goPrevious();
          break;
        case ' ':
          event.preventDefault();
          dispatch(togglePlaying());
          break;
        case 'Escape':
          event.preventDefault();
          handleClose();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [dispatch, goNext, goPrevious, handleClose]);

  // Keep the audio element in sync with playback and mute state.
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.muted = isMuted;
    if (isPlaying && !isMuted) {
      // Autoplay can be refused; the story should keep running regardless.
      void audio.play().catch(() => undefined);
    } else {
      audio.pause();
    }
  }, [isPlaying, isMuted, memoryId]);

  const touchStartX = useRef<number | null>(null);

  const onPointerDown = (event: React.PointerEvent) => {
    touchStartX.current = event.clientX;
  };

  const onPointerUp = (event: React.PointerEvent) => {
    const startX = touchStartX.current;
    touchStartX.current = null;
    if (startX === null) return;

    const deltaX = event.clientX - startX;
    if (Math.abs(deltaX) < SWIPE_THRESHOLD) return;
    if (deltaX < 0) goNext();
    else goPrevious();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={memory?.title ?? 'Memory'}
      className="fixed inset-0 z-50 flex flex-col bg-black"
    >
      {/* Segmented progress: one bar per photo, the active one filling live. */}
      <div className="flex gap-1 px-4 pt-3" aria-hidden>
        {Array.from({ length: total }).map((_, index) => (
          <div
            key={index}
            className="h-0.5 flex-1 overflow-hidden rounded-full bg-white/25"
          >
            <div
              className="h-full bg-white"
              style={{
                width:
                  index < safeIndex
                    ? '100%'
                    : index === safeIndex
                      ? `${progress * 100}%`
                      : '0%',
              }}
            />
          </div>
        ))}
      </div>

      <div className="flex items-start justify-between gap-4 px-4 py-3">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold text-white">
            {memory?.title ?? 'Loading…'}
          </h2>
          {memory && (
            <p className="truncate text-sm text-white/60">
              {formatMemorySubtitle(memory)}
            </p>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-1">
          {total > 0 && (
            <span className="mr-1 text-sm text-white/60 tabular-nums">
              {safeIndex + 1} / {total}
            </span>
          )}
          <button
            type="button"
            onClick={() => dispatch(togglePlaying())}
            aria-label={isPlaying ? 'Pause' : 'Play'}
            className="rounded-full p-2 text-white/80 hover:bg-white/10 hover:text-white"
          >
            {isPlaying ? (
              <Pause className="h-5 w-5" />
            ) : (
              <Play className="h-5 w-5" />
            )}
          </button>
          {musicEnabled && (
            <button
              type="button"
              onClick={() => dispatch(toggleMuted())}
              aria-label={isMuted ? 'Unmute music' : 'Mute music'}
              className="rounded-full p-2 text-white/80 hover:bg-white/10 hover:text-white"
            >
              {isMuted ? (
                <VolumeX className="h-5 w-5" />
              ) : (
                <Volume2 className="h-5 w-5" />
              )}
            </button>
          )}
          <button
            type="button"
            onClick={() => navigate(`/${ROUTES.MEMORIES_SETTINGS}`)}
            aria-label="Memory settings"
            className="rounded-full p-2 text-white/80 hover:bg-white/10 hover:text-white"
          >
            <Settings className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Close memory"
            className="rounded-full p-2 text-white/80 hover:bg-white/10 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div
        className="relative min-h-0 flex-1 touch-pan-y select-none"
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
      >
        {isLoading && (
          <div className="flex h-full items-center justify-center text-white/60">
            Loading memory…
          </div>
        )}

        {isError && (
          <div className="flex h-full items-center justify-center text-white/60">
            This memory could not be loaded.
          </div>
        )}

        {!isLoading && !isError && currentImage && (
          <>
            <img
              key={currentImage.id}
              src={getMemoryImageUrl(currentImage.path)}
              alt=""
              onError={handleImageError}
              className="h-full w-full object-contain"
            />
            {currentImage.captured_at && (
              <p className="absolute inset-x-0 bottom-4 text-center text-sm text-white/70 drop-shadow">
                {formatMemoryDate(currentImage.captured_at)}
              </p>
            )}
          </>
        )}

        {total > 1 && (
          <>
            <button
              type="button"
              onClick={goPrevious}
              disabled={safeIndex === 0}
              aria-label="Previous photo"
              className={cn(
                'absolute top-1/2 left-3 -translate-y-1/2 rounded-full bg-black/40 p-2 text-white/80 backdrop-blur-sm hover:bg-black/60 hover:text-white',
                safeIndex === 0 && 'pointer-events-none opacity-30',
              )}
            >
              <ChevronLeft className="h-6 w-6" />
            </button>
            <button
              type="button"
              onClick={goNext}
              aria-label="Next photo"
              className="absolute top-1/2 right-3 -translate-y-1/2 rounded-full bg-black/40 p-2 text-white/80 backdrop-blur-sm hover:bg-black/60 hover:text-white"
            >
              <ChevronRight className="h-6 w-6" />
            </button>
          </>
        )}
      </div>

      <MemoryFilmstrip
        memories={memories}
        activeMemoryId={memoryId}
        onSelect={(id) => {
          dispatch(openMemory(id));
          dispatch(setPlaying(true));
        }}
      />

      {musicEnabled && (
        <audio
          ref={audioRef}
          src={STORY_AUDIO_SRC}
          loop
          muted={isMuted}
          preload="none"
        />
      )}
    </div>
  );
};

export default MemoryStoryViewer;
