/**
 * MemoriesPage Component
 *
 * Main page for the Memories feature.
 * Displays memories in sections: On This Day, Recent, This Year, All Memories, Weekends.
 * Includes filter tabs for All/Location/Date/Weekends memories.
 *
 * Uses Tanstack Query for data fetching (not Redux async thunks).
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { showInfoDialog } from '@/features/infoDialogSlice';
import {
  useAllMemories,
  useRecentMemories,
  useYearMemories,
  useOnThisDay,
  useWeeklyMemories,
} from '@/hooks/useMemories';
import { MemoryCard } from './MemoryCard';
import { FeaturedMemoryCard } from './FeaturedMemoryCard';
import type { Memory, WeeklyMemory } from '@/api/api-functions/memories';
import { convertFileSrc } from '@tauri-apps/api/core';
import { ArrowLeft } from 'lucide-react';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { setImages, setCurrentViewIndex } from '@/features/imageSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { showLoader, hideLoader } from '@/features/loaderSlice';

/**
 * Loading skeleton for memory cards
 */
const MemoryCardSkeleton: React.FC = () => (
  <div className="animate-pulse overflow-hidden rounded-lg border shadow-md">
    <div className="bg-muted h-48 w-full" />
    <div className="space-y-3 p-4">
      <div className="bg-muted h-5 w-3/4 rounded" />
      <div className="bg-muted h-4 w-1/2 rounded" />
      <div className="bg-muted h-4 w-2/3 rounded" />
    </div>
  </div>
);

/**
 * Featured card skeleton for On This Day
 */
const FeaturedSkeleton: React.FC = () => (
  <div className="animate-pulse overflow-hidden rounded-xl border shadow-lg">
    <div className="bg-muted h-64 w-full md:h-96 lg:h-[28rem]" />
    <div className="space-y-3 p-4">
      <div className="bg-muted h-6 w-1/2 rounded" />
    </div>
  </div>
);

/**
 * Section header component with date-based styling
 */
const SectionHeader: React.FC<{
  title: string;
  count?: number;
  date?: string;
}> = ({ title, count, date }) => (
  <div className="mb-6">
    <h2 className="flex items-center text-xl font-semibold text-gray-800 dark:text-gray-200">
      <div className="bg-primary mr-2 h-6 w-1"></div>
      {date || title}
      {count !== undefined && count > 0 && (
        <div className="mt-1 ml-2 text-sm font-normal text-gray-500">
          {count} {count === 1 ? 'memory' : 'memories'}
        </div>
      )}
    </h2>
  </div>
);

/**
 * Error message component with retry button
 */
const ErrorMessage: React.FC<{ message: string; onRetry: () => void }> = ({
  message,
  onRetry,
}) => (
  <div className="border-destructive/50 bg-destructive/10 rounded-lg border p-6 text-center">
    <div className="flex flex-col items-center space-y-3">
      <svg
        className="text-destructive h-12 w-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p className="text-destructive font-medium">{message}</p>
      <button
        onClick={onRetry}
        className="rounded-lg bg-red-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-red-700"
      >
        Try Again
      </button>
    </div>
  </div>
);

/**
 * Empty state component
 */
const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="border-border bg-muted/50 rounded-lg border-2 border-dashed p-12 text-center">
    <svg
      className="text-muted-foreground mx-auto mb-4 h-16 w-16"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
    <p className="text-muted-foreground text-lg">{message}</p>
  </div>
);

/**
 * Format a date string (YYYY-MM-DD) to a readable form.
 */
function formatWeekendDate(dateStr: string): string {
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Card for a single weekend memory cluster
 */
const WeekendMemoryCard: React.FC<{
  memory: WeeklyMemory;
  onClick: (memory: WeeklyMemory) => void;
}> = ({ memory, onClick }) => {
  const firstImage = memory.images[0];
  const thumbnailSrc = firstImage?.thumbnailPath
    ? convertFileSrc(firstImage.thumbnailPath)
    : firstImage?.path
      ? convertFileSrc(firstImage.path)
      : '/photo.png';

  const sameDay = memory.start_date === memory.end_date;
  const dateLabel = sameDay
    ? formatWeekendDate(memory.start_date)
    : `${formatWeekendDate(memory.start_date)} – ${formatWeekendDate(memory.end_date)}`;

  return (
    <div
      onClick={() => onClick(memory)}
      className="group bg-card transform cursor-pointer overflow-hidden rounded-lg border shadow-md transition-all duration-200 hover:scale-[1.02] hover:shadow-xl"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(memory);
        }
      }}
      aria-label={`View weekend memory: ${dateLabel}`}
    >
      {/* Thumbnail */}
      <div className="bg-muted relative h-48 w-full overflow-hidden">
        <img
          src={thumbnailSrc}
          alt="Weekend memory"
          onError={(e) => {
            e.currentTarget.src = '/photo.png';
          }}
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
          loading="lazy"
        />
        {/* Weekend badge */}
        <div className="absolute top-2 left-2 flex items-center gap-1 rounded-full bg-black/70 px-2 py-1 text-xs text-white backdrop-blur-sm">
          <svg
            className="h-3 w-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
            />
          </svg>
          <span>Weekend</span>
        </div>
        {/* Photo count badge */}
        <div className="absolute top-2 right-2 rounded-full bg-black/70 px-2 py-1 text-xs text-white backdrop-blur-sm">
          {memory.images.length}{' '}
          {memory.images.length === 1 ? 'photo' : 'photos'}
        </div>
      </div>

      {/* Card content */}
      <div className="space-y-1 p-4">
        <h3 className="line-clamp-1 text-lg font-semibold">
          Happy Weekends 🎉
        </h3>
        <p className="text-muted-foreground line-clamp-1 text-sm">
          {dateLabel}
        </p>
      </div>
    </div>
  );
};

/**
 * Full-screen detail view for a selected weekend memory.
 * Mirrors MemoryDetail: loads images into Redux, renders ImageCard grid + MediaView.
 */
const WeekendMemoryDetail: React.FC<{
  memory: WeeklyMemory;
  onClose: () => void;
}> = ({ memory, onClose }) => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);

  const sameDay = memory.start_date === memory.end_date;
  const dateLabel = sameDay
    ? formatWeekendDate(memory.start_date)
    : `${formatWeekendDate(memory.start_date)} – ${formatWeekendDate(memory.end_date)}`;

  // Load images into Redux on mount (same pattern as MemoryDetail)
  useEffect(() => {
    dispatch(showLoader('Loading weekend memory'));

    const formattedImages = memory.images.map((img) => ({
      id: img.id,
      path: img.path,
      thumbnailPath: img.thumbnailPath,
      folder_id: '',
      isTagged: false,
      isFavourite: false,
      tags: [],
      metadata: {
        name: img.path.split('/').pop() || img.path.split('\\').pop() || '',
        date_created: null,
        width: 0,
        height: 0,
        file_location: img.path,
        file_size: 0,
        item_type: 'image' as const,
      },
    }));

    requestAnimationFrame(() => {
      dispatch(setImages(formattedImages));
      dispatch(hideLoader());
    });
  }, [memory, dispatch]);

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="bg-background border-b px-6 py-3">
        <div className="mb-3">
          <button
            onClick={onClose}
            className="hover:bg-secondary flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Memories
          </button>
        </div>
        <div>
          <h1 className="flex items-center text-xl font-semibold text-gray-800 dark:text-gray-200">
            <div className="bg-primary mr-2 h-6 w-1" />
            Happy Weekends 🎉
            <div className="mt-1 ml-2 text-sm font-normal text-gray-500">
              {dateLabel}
            </div>
          </h1>
        </div>
        <p className="text-muted-foreground mt-1 ml-5 text-sm">
          {memory.images.length}{' '}
          {memory.images.length === 1 ? 'photo' : 'photos'}
        </p>
      </div>

      {/* Scrollable Images Grid — same layout as MemoryDetail */}
      <div className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto px-6 py-6">
        {memory.images.length === 0 ? (
          <EmptyState message="No photos in this weekend memory." />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {images.map((image, index) => (
              <ImageCard
                key={image.id}
                image={image}
                imageIndex={index}
                className="w-full"
                onClick={() => dispatch(setCurrentViewIndex(index))}
              />
            ))}
          </div>
        )}
      </div>

      {/* Full-screen viewer */}
      {isImageViewOpen && (
        <MediaView
          type="image"
          onToggleFavorite={async () => {}}
          images={images}
        />
      )}
    </div>
  );
};

/**
 * Main Memories Page Component
 * Uses Tanstack Query hooks for data fetching
 */
export const MemoriesPage: React.FC = () => {
  const dispatch = useDispatch();

  // Tanstack Query hooks
  const allMemoriesQuery = useAllMemories();
  const recentMemoriesQuery = useRecentMemories(30);
  const yearMemoriesQuery = useYearMemories(365);
  const onThisDayQuery = useOnThisDay();
  const weeklyMemoriesQuery = useWeeklyMemories();

  // Extract data
  const allMemories = (allMemoriesQuery.data?.data?.memories as any) || [];
  const recentMemories =
    (recentMemoriesQuery.data?.data?.memories as any) || [];
  const yearMemories = (yearMemoriesQuery.data?.data?.memories as any) || [];
  const onThisDayImages = (onThisDayQuery.data?.data?.images as any) || [];
  const onThisDayMeta = onThisDayQuery.data?.data
    ? {
        today: (onThisDayQuery.data.data as any).today,
        years: (onThisDayQuery.data.data as any).years,
      }
    : null;

  // Weekend memories – the backend returns them directly (no .data wrapper)
  const weeklyMemories: WeeklyMemory[] =
    weeklyMemoriesQuery.data?.weekly_memories || [];

  // Loading states
  const loading = {
    all: allMemoriesQuery.isLoading,
    recent: recentMemoriesQuery.isLoading,
    year: yearMemoriesQuery.isLoading,
    onThisDay: onThisDayQuery.isLoading,
    weekends: weeklyMemoriesQuery.isLoading,
  };

  // Error handling with InfoDialog
  useEffect(() => {
    if (allMemoriesQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading Memories',
          message: allMemoriesQuery.errorMessage || 'Failed to load memories',
          variant: 'error',
        }),
      );
    }
  }, [allMemoriesQuery.isError, allMemoriesQuery.errorMessage, dispatch]);

  useEffect(() => {
    if (recentMemoriesQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading Recent Memories',
          message:
            recentMemoriesQuery.errorMessage ||
            'Failed to load recent memories',
          variant: 'error',
        }),
      );
    }
  }, [recentMemoriesQuery.isError, recentMemoriesQuery.errorMessage, dispatch]);

  useEffect(() => {
    if (yearMemoriesQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading Year Memories',
          message:
            yearMemoriesQuery.errorMessage || 'Failed to load year memories',
          variant: 'error',
        }),
      );
    }
  }, [yearMemoriesQuery.isError, yearMemoriesQuery.errorMessage, dispatch]);

  useEffect(() => {
    if (onThisDayQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading On This Day',
          message: onThisDayQuery.errorMessage || 'Failed to load On This Day',
          variant: 'error',
        }),
      );
    }
  }, [onThisDayQuery.isError, onThisDayQuery.errorMessage, dispatch]);

  useEffect(() => {
    if (weeklyMemoriesQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading Weekend Memories',
          message:
            weeklyMemoriesQuery.errorMessage ||
            'Failed to load weekend memories',
          variant: 'error',
        }),
      );
    }
  }, [weeklyMemoriesQuery.isError, weeklyMemoriesQuery.errorMessage, dispatch]);

  // Filter state: 'all' | 'location' | 'date' | 'weekends'
  const [filter, setFilter] = useState<
    'all' | 'location' | 'date' | 'weekends'
  >('all');

  // Selected weekend memory for detail view
  const [selectedWeekend, setSelectedWeekend] = useState<WeeklyMemory | null>(
    null,
  );

  const handleWeekendCardClick = useCallback((memory: WeeklyMemory) => {
    setSelectedWeekend(memory);
  }, []);

  const handleCloseWeekendDetail = useCallback(() => {
    setSelectedWeekend(null);
  }, []);

  // Filter out memories with only 1 image (same as backend min_images=2)
  const memoriesWithMultipleImages = (memories: Memory[]) =>
    memories.filter((m) => m.image_count >= 2);

  // Calculate counts (only memories with 2+ images)
  const totalCount = memoriesWithMultipleImages(allMemories).length;

  const locationCount =
    (allMemoriesQuery.data as any)?.total_location ??
    memoriesWithMultipleImages(allMemories).filter(
      (m) => m.location_name !== null,
    ).length;

  const dateCount = totalCount - locationCount;

  const weekendsCount = weeklyMemories.length;

  // Simple filter function
  const applyFilter = (memories: Memory[]) => {
    // First filter out single-image memories
    const multiImageMemories = memoriesWithMultipleImages(memories);

    if (filter === 'location') {
      return multiImageMemories.filter((m) => m.location_name !== null);
    }
    if (filter === 'date') {
      return multiImageMemories.filter((m) => m.location_name === null);
    }
    return multiImageMemories; // 'all' and 'weekends' don't filter regular memories
  };

  // Apply filter
  const filteredRecentMemories = applyFilter(recentMemories);
  const filteredYearMemories = applyFilter(yearMemories);
  const filteredAllMemories = applyFilter(allMemories);

  // Retry handlers
  const handleRetryAll = () => allMemoriesQuery.refetch();
  const handleRetryRecent = () => recentMemoriesQuery.refetch();
  const handleRetryYear = () => yearMemoriesQuery.refetch();
  const handleRetryOnThisDay = () => onThisDayQuery.refetch();
  const handleRetryWeekends = () => weeklyMemoriesQuery.refetch();

  // Check if any data exists
  const hasAnyData =
    onThisDayImages.length > 0 ||
    recentMemories.length > 0 ||
    yearMemories.length > 0 ||
    allMemories.length > 0 ||
    weeklyMemories.length > 0;

  // If a weekend memory detail is selected, show it full-screen
  if (selectedWeekend) {
    return (
      <WeekendMemoryDetail
        memory={selectedWeekend}
        onClose={handleCloseWeekendDetail}
      />
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto p-6">
        {/* Page Title - matching Home/AI Tagging style */}
        <h1 className="mb-6 text-2xl font-bold">Memories</h1>

        <div className="space-y-12">
          {/* Filter Buttons */}
          {hasAnyData && (
            <div className="mb-6 flex flex-wrap justify-start gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  filter === 'all'
                    ? 'bg-foreground text-background'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                All ({totalCount})
              </button>
              <button
                onClick={() => setFilter('location')}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  filter === 'location'
                    ? 'bg-foreground text-background'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                Location ({locationCount})
              </button>
              <button
                onClick={() => setFilter('date')}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  filter === 'date'
                    ? 'bg-foreground text-background'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                Date ({dateCount})
              </button>
              <button
                onClick={() => setFilter('weekends')}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  filter === 'weekends'
                    ? 'bg-foreground text-background'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                Weekends {weekendsCount > 0 ? `(${weekendsCount})` : ''}
              </button>
            </div>
          )}

          {/* Global Loading State */}
          {!hasAnyData && loading.all && (
            <div className="space-y-12">
              <FeaturedSkeleton />
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                {[...Array(8)].map((_, i) => (
                  <MemoryCardSkeleton key={i} />
                ))}
              </div>
            </div>
          )}

          {/* Global Error State */}
          {!hasAnyData && allMemoriesQuery.isError && (
            <ErrorMessage
              message={
                allMemoriesQuery.errorMessage || 'Failed to load memories'
              }
              onRetry={handleRetryAll}
            />
          )}

          {/* Global Empty State */}
          {!hasAnyData && !loading.all && !allMemoriesQuery.isError && (
            <EmptyState message="No memories found. Upload photos with location data to get started!" />
          )}

          {/* ====================================================================
            WEEKENDS SECTION  (shown when Weekends filter is active)
            ==================================================================== */}
          {filter === 'weekends' && (
            <section className="space-y-6">
              <SectionHeader
                title="Weekend Memories"
                count={weeklyMemories.length}
              />
              {loading.weekends ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                  {[...Array(4)].map((_, i) => (
                    <MemoryCardSkeleton key={i} />
                  ))}
                </div>
              ) : weeklyMemoriesQuery.isError ? (
                <ErrorMessage
                  message={
                    weeklyMemoriesQuery.errorMessage ||
                    'Failed to load weekend memories'
                  }
                  onRetry={handleRetryWeekends}
                />
              ) : weeklyMemories.length === 0 ? (
                <EmptyState message="No weekend memories found. Add photos taken on weekends to get started!" />
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                  {weeklyMemories.map((wm) => (
                    <WeekendMemoryCard
                      key={wm.mem_id}
                      memory={wm}
                      onClick={handleWeekendCardClick}
                    />
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Hide all other sections while Weekends tab is active */}
          {filter !== 'weekends' && (
            <>
              {/* ====================================================================
                SECTION 1: On This Day
                ==================================================================== */}
              {onThisDayImages.length > 0 && onThisDayMeta && (
                <section className="space-y-6">
                  <SectionHeader title="On This Day" />
                  {loading.onThisDay ? (
                    <FeaturedSkeleton />
                  ) : onThisDayQuery.isError ? (
                    <ErrorMessage
                      message={
                        onThisDayQuery.errorMessage ||
                        'Failed to load On This Day'
                      }
                      onRetry={handleRetryOnThisDay}
                    />
                  ) : (
                    <FeaturedMemoryCard
                      images={onThisDayImages}
                      today={onThisDayMeta.today}
                      years={onThisDayMeta.years}
                      memoryId="on-this-day"
                    />
                  )}
                </section>
              )}

              {/* ====================================================================
                SECTION 2: Recent Memories (Last 30 days)
                ==================================================================== */}
              {filteredRecentMemories.length > 0 && (
                <section className="space-y-6">
                  <SectionHeader
                    title="Recent Memories"
                    count={filteredRecentMemories.length}
                  />
                  {loading.recent ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                      {[...Array(4)].map((_, i) => (
                        <MemoryCardSkeleton key={i} />
                      ))}
                    </div>
                  ) : recentMemoriesQuery.isError ? (
                    <ErrorMessage
                      message={
                        recentMemoriesQuery.errorMessage ||
                        'Failed to load recent memories'
                      }
                      onRetry={handleRetryRecent}
                    />
                  ) : (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                      {filteredRecentMemories.map((memory: Memory) => (
                        <MemoryCard key={memory.memory_id} memory={memory} />
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* ====================================================================
                SECTION 3: Past Year (Last 365 days)
                ==================================================================== */}
              {filteredYearMemories.length > 0 && (
                <section className="space-y-6">
                  <SectionHeader
                    title="Past Year"
                    date="Past Year"
                    count={filteredYearMemories.length}
                  />
                  {loading.year ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                      {[...Array(4)].map((_, i) => (
                        <MemoryCardSkeleton key={i} />
                      ))}
                    </div>
                  ) : yearMemoriesQuery.isError ? (
                    <ErrorMessage
                      message={
                        yearMemoriesQuery.errorMessage ||
                        'Failed to load year memories'
                      }
                      onRetry={handleRetryYear}
                    />
                  ) : (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                      {filteredYearMemories.map((memory: Memory) => (
                        <MemoryCard key={memory.memory_id} memory={memory} />
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* ====================================================================
                SECTION 4: All Memories
                ==================================================================== */}
              {filteredAllMemories.length > 0 && (
                <section className="space-y-6">
                  <SectionHeader
                    title="All Memories"
                    date="All time"
                    count={filteredAllMemories.length}
                  />
                  {loading.all ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                      {[...Array(8)].map((_, i) => (
                        <MemoryCardSkeleton key={i} />
                      ))}
                    </div>
                  ) : allMemoriesQuery.isError ? (
                    <ErrorMessage
                      message={
                        allMemoriesQuery.errorMessage ||
                        'Failed to load all memories'
                      }
                      onRetry={handleRetryAll}
                    />
                  ) : (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                      {filteredAllMemories.map((memory: Memory) => (
                        <MemoryCard key={memory.memory_id} memory={memory} />
                      ))}
                    </div>
                  )}
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemoriesPage;
