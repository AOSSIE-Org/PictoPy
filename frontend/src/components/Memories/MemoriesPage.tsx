/**
 * MemoriesPage Component
 *
 * Main page for the Memories feature.
 * Displays memories in sections: On This Day, Recent, This Year, All Memories.
 * Includes filter tabs for All/Location/Date memories.
 *
 * Uses Tanstack Query for data fetching (not Redux async thunks).
 */

import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { showInfoDialog } from '@/features/infoDialogSlice';
import {
  useAllMemories,
  useRecentMemories,
  useYearMemories,
  useOnThisDay,
} from '@/hooks/useMemories';
import { MemoryCard } from './MemoryCard';
import { FeaturedMemoryCard } from './FeaturedMemoryCard';
import type { Memory } from '@/services/memoriesApi';

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

  // Extract data
  const allMemories = allMemoriesQuery.data?.memories || [];
  const recentMemories = recentMemoriesQuery.data?.memories || [];
  const yearMemories = yearMemoriesQuery.data?.memories || [];
  const onThisDayImages = onThisDayQuery.data?.images || [];
  const onThisDayMeta = onThisDayQuery.data
    ? {
        today: onThisDayQuery.data.today,
        years: onThisDayQuery.data.years,
      }
    : null;

  // Loading states
  const loading = {
    all: allMemoriesQuery.isLoading,
    recent: recentMemoriesQuery.isLoading,
    year: yearMemoriesQuery.isLoading,
    onThisDay: onThisDayQuery.isLoading,
  };

  // Error handling with InfoDialog
  useEffect(() => {
    if (allMemoriesQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading Memories',
          message: allMemoriesQuery.error?.message || 'Failed to load memories',
          variant: 'error',
        }),
      );
    }
  }, [allMemoriesQuery.isError, allMemoriesQuery.error, dispatch]);

  useEffect(() => {
    if (recentMemoriesQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading Recent Memories',
          message:
            recentMemoriesQuery.error?.message ||
            'Failed to load recent memories',
          variant: 'error',
        }),
      );
    }
  }, [recentMemoriesQuery.isError, recentMemoriesQuery.error, dispatch]);

  useEffect(() => {
    if (yearMemoriesQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading Year Memories',
          message:
            yearMemoriesQuery.error?.message || 'Failed to load year memories',
          variant: 'error',
        }),
      );
    }
  }, [yearMemoriesQuery.isError, yearMemoriesQuery.error, dispatch]);

  useEffect(() => {
    if (onThisDayQuery.isError) {
      dispatch(
        showInfoDialog({
          title: 'Error Loading On This Day',
          message:
            onThisDayQuery.error?.message || 'Failed to load On This Day',
          variant: 'error',
        }),
      );
    }
  }, [onThisDayQuery.isError, onThisDayQuery.error, dispatch]);

  // Simple filter state: 'all' | 'location' | 'date'
  const [filter, setFilter] = useState<'all' | 'location' | 'date'>('all');

  // Filter out memories with only 1 image (same as backend min_images=2)
  const memoriesWithMultipleImages = (memories: Memory[]) =>
    memories.filter((m) => m.image_count >= 2);

  // Calculate counts (only memories with 2+ images)
  const totalCount = memoriesWithMultipleImages(allMemories).length;
  const locationCount = memoriesWithMultipleImages(allMemories).filter(
    (m) => m.center_lat != null && m.center_lon != null,
  ).length;
  const dateCount = memoriesWithMultipleImages(allMemories).filter(
    (m) => m.center_lat == null || m.center_lon == null,
  ).length;

  // Simple filter function
  const applyFilter = (memories: Memory[]) => {
    // First filter out single-image memories
    const multiImageMemories = memoriesWithMultipleImages(memories);

    if (filter === 'location') {
      return multiImageMemories.filter(
        (m) => m.center_lat != null && m.center_lon != null,
      );
    }
    if (filter === 'date') {
      return multiImageMemories.filter(
        (m) => m.center_lat == null || m.center_lon == null,
      );
    }
    return multiImageMemories; // 'all'
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

  // Check if any data exists
  const hasAnyData =
    onThisDayImages.length > 0 ||
    recentMemories.length > 0 ||
    yearMemories.length > 0 ||
    allMemories.length > 0;

  return (
    <div className="flex h-full flex-col">
      <div className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto p-6">
        {/* Page Title - matching Home/AI Tagging style */}
        <h1 className="mb-6 text-2xl font-bold">Memories</h1>

        <div className="space-y-12">
          {/* Filter Buttons */}
          {hasAnyData && (
            <div className="mb-6 flex justify-start gap-2">
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
                allMemoriesQuery.error?.message || 'Failed to load memories'
              }
              onRetry={handleRetryAll}
            />
          )}

          {/* Global Empty State */}
          {!hasAnyData && !loading.all && !allMemoriesQuery.isError && (
            <EmptyState message="No memories found. Upload photos with location data to get started!" />
          )}

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
                    onThisDayQuery.error?.message ||
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
                    recentMemoriesQuery.error?.message ||
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
                    yearMemoriesQuery.error?.message ||
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
                    allMemoriesQuery.error?.message ||
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
        </div>
      </div>
    </div>
  );
};

export default MemoriesPage;
