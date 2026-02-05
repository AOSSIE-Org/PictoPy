/**
 * MemoriesPage Component
 *
 * Main page for the Memories feature.
 * Displays memories in sections: On This Day, Recent, This Year, All Memories.
 * Includes filter tabs for All/Location/Date memories.
 *
 * Layout mimics Google Photos Memories with smart feed organization.
 */

import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchAllMemoriesData,
  fetchAllMemories,
  fetchRecentMemories,
  fetchYearMemories,
  fetchOnThisDay,
  setSelectedMemory,
  selectOnThisDayImages,
  selectOnThisDayMeta,
  selectRecentMemories,
  selectYearMemories,
  selectAllMemories,
  selectMemoriesLoading,
  selectMemoriesError,
  selectTotalMemoryCount,
} from '@/store/slices/memoriesSlice';
import { MemoryCard } from './MemoryCard';
import { FeaturedMemoryCard } from './FeaturedMemoryCard';
import { MemoryViewer } from './MemoryViewer.tsx';
import type { Memory } from '@/services/memoriesApi';

/**
 * Loading skeleton for memory cards
 */
const MemoryCardSkeleton: React.FC = () => (
  <div className="animate-pulse overflow-hidden rounded-lg bg-white shadow-md dark:bg-gray-800">
    <div className="h-48 w-full bg-gray-300 dark:bg-gray-700" />
    <div className="space-y-3 p-4">
      <div className="h-5 w-3/4 rounded bg-gray-300 dark:bg-gray-700" />
      <div className="h-4 w-1/2 rounded bg-gray-300 dark:bg-gray-700" />
      <div className="h-4 w-2/3 rounded bg-gray-300 dark:bg-gray-700" />
    </div>
  </div>
);

/**
 * Featured card skeleton for On This Day
 */
const FeaturedSkeleton: React.FC = () => (
  <div className="animate-pulse overflow-hidden rounded-xl bg-white shadow-lg dark:bg-gray-800">
    <div className="h-64 w-full bg-gradient-to-br from-gray-300 to-gray-400 md:h-96 lg:h-[28rem] dark:from-gray-700 dark:to-gray-800" />
    <div className="space-y-3 p-4">
      <div className="h-6 w-1/2 rounded bg-gray-300 dark:bg-gray-700" />
    </div>
  </div>
);

/**
 * Section header component
 */
const SectionHeader: React.FC<{ title: string; count?: number }> = ({
  title,
  count,
}) => (
  <h2 className="mb-6 text-2xl font-bold text-gray-900 md:text-3xl dark:text-white">
    {title}
    {count !== undefined && count > 0 && (
      <span className="ml-2 text-lg text-gray-500 dark:text-gray-400">
        ({count})
      </span>
    )}
  </h2>
);

/**
 * Error message component with retry button
 */
const ErrorMessage: React.FC<{ message: string; onRetry: () => void }> = ({
  message,
  onRetry,
}) => (
  <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/20">
    <div className="flex flex-col items-center space-y-3">
      <svg
        className="h-12 w-12 text-red-500 dark:text-red-400"
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
      <p className="font-medium text-red-800 dark:text-red-200">{message}</p>
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
  <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-12 text-center dark:border-gray-700 dark:bg-gray-800">
    <svg
      className="mx-auto mb-4 h-16 w-16 text-gray-400 dark:text-gray-600"
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
    <p className="text-lg text-gray-600 dark:text-gray-400">{message}</p>
  </div>
);

/**
 * Main Memories Page Component
 * SIMPLIFIED: Basic All/Location/Date filter buttons
 */
export const MemoriesPage: React.FC = () => {
  const dispatch = useAppDispatch();

  // Selectors
  const onThisDayImages = useAppSelector(selectOnThisDayImages);
  const onThisDayMeta = useAppSelector(selectOnThisDayMeta);
  const recentMemories = useAppSelector(selectRecentMemories);
  const yearMemories = useAppSelector(selectYearMemories);
  const allMemories = useAppSelector(selectAllMemories);
  const loading = useAppSelector(selectMemoriesLoading);
  const error = useAppSelector(selectMemoriesError);
  const totalCount = useAppSelector(selectTotalMemoryCount);

  // Simple filter state: 'all' | 'location' | 'date'
  const [filter, setFilter] = useState<'all' | 'location' | 'date'>('all');

  // Calculate counts
  const locationCount = allMemories.filter(
    (m) => m.center_lat != null && m.center_lon != null,
  ).length;
  const dateCount = allMemories.filter(
    (m) => m.center_lat == null || m.center_lon == null,
  ).length;

  // Simple filter function
  const applyFilter = (memories: Memory[]) => {
    if (filter === 'location') {
      return memories.filter(
        (m) => m.center_lat != null && m.center_lon != null,
      );
    }
    if (filter === 'date') {
      return memories.filter(
        (m) => m.center_lat == null || m.center_lon == null,
      );
    }
    return memories; // 'all'
  };

  // Apply filter
  const filteredRecentMemories = applyFilter(recentMemories);
  const filteredYearMemories = applyFilter(yearMemories);
  const filteredAllMemories = applyFilter(allMemories);

  // Fetch all data on mount
  useEffect(() => {
    dispatch(fetchAllMemoriesData());
  }, [dispatch]);

  // Handle memory card click
  const handleMemoryClick = (memory: Memory) => {
    dispatch(setSelectedMemory(memory));
  };

  // Handle On This Day click - create a temporary memory from images
  const handleOnThisDayClick = () => {
    if (onThisDayImages.length > 0 && onThisDayMeta) {
      const tempMemory: Memory = {
        memory_id: 'on-this-day',
        title: `On This Day - ${onThisDayMeta.today}`,
        description: `Photos from ${onThisDayMeta.years.join(', ')}`,
        location_name: 'Various locations',
        date_start: onThisDayImages[0]?.captured_at || null,
        date_end:
          onThisDayImages[onThisDayImages.length - 1]?.captured_at || null,
        image_count: onThisDayImages.length,
        images: onThisDayImages,
        thumbnail_image_id: onThisDayImages[0]?.id || '',
        center_lat: onThisDayImages[0]?.latitude ?? null,
        center_lon: onThisDayImages[0]?.longitude ?? null,
      };
      dispatch(setSelectedMemory(tempMemory));
    }
  };

  // Retry handlers
  const handleRetryAll = () => dispatch(fetchAllMemories());
  const handleRetryRecent = () => dispatch(fetchRecentMemories(30));
  const handleRetryYear = () => dispatch(fetchYearMemories(365));
  const handleRetryOnThisDay = () => dispatch(fetchOnThisDay());

  // Check if any data exists
  const hasAnyData =
    onThisDayImages.length > 0 ||
    recentMemories.length > 0 ||
    yearMemories.length > 0 ||
    allMemories.length > 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white shadow-sm dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <svg
                className="h-8 w-8 text-blue-600 dark:text-blue-400"
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
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Memories
                {totalCount > 0 && (
                  <span className="ml-2 text-lg text-gray-500 dark:text-gray-400">
                    ({totalCount})
                  </span>
                )}
              </h1>
            </div>

            {/* Refresh button */}
            <button
              onClick={() => dispatch(fetchAllMemoriesData())}
              className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-blue-400"
              aria-label="Refresh memories"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl space-y-12 px-4 py-8 sm:px-6 lg:px-8">
        {/* Simple Filter Buttons */}
        {hasAnyData && (
          <div className="flex justify-center gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`rounded-lg px-4 py-2 font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => setFilter('location')}
              className={`rounded-lg px-4 py-2 font-medium transition-colors ${
                filter === 'location'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Location ({locationCount})
            </button>
            <button
              onClick={() => setFilter('date')}
              className={`rounded-lg px-4 py-2 font-medium transition-colors ${
                filter === 'date'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
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
        {!hasAnyData && error.all && (
          <ErrorMessage message={error.all} onRetry={handleRetryAll} />
        )}

        {/* Global Empty State */}
        {!hasAnyData && !loading.all && !error.all && (
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
            ) : error.onThisDay ? (
              <ErrorMessage
                message={error.onThisDay}
                onRetry={handleRetryOnThisDay}
              />
            ) : (
              <FeaturedMemoryCard
                images={onThisDayImages}
                today={onThisDayMeta.today}
                years={onThisDayMeta.years}
                onClick={handleOnThisDayClick}
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
            ) : error.recent ? (
              <ErrorMessage
                message={error.recent}
                onRetry={handleRetryRecent}
              />
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                {filteredRecentMemories.map((memory: Memory) => (
                  <MemoryCard
                    key={memory.memory_id}
                    memory={memory}
                    onClick={handleMemoryClick}
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {/* ====================================================================
            SECTION 3: This Year
            ==================================================================== */}
        {filteredYearMemories.length > 0 && (
          <section className="space-y-6">
            <SectionHeader
              title="This Year"
              count={filteredYearMemories.length}
            />
            {loading.year ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                  <MemoryCardSkeleton key={i} />
                ))}
              </div>
            ) : error.year ? (
              <ErrorMessage message={error.year} onRetry={handleRetryYear} />
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                {filteredYearMemories.map((memory: Memory) => (
                  <MemoryCard
                    key={memory.memory_id}
                    memory={memory}
                    onClick={handleMemoryClick}
                  />
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
              count={filteredAllMemories.length}
            />
            {loading.all ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                {[...Array(8)].map((_, i) => (
                  <MemoryCardSkeleton key={i} />
                ))}
              </div>
            ) : error.all ? (
              <ErrorMessage message={error.all} onRetry={handleRetryAll} />
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:grid-cols-4">
                {filteredAllMemories.map((memory: Memory) => (
                  <MemoryCard
                    key={memory.memory_id}
                    memory={memory}
                    onClick={handleMemoryClick}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      {/* Memory Viewer Modal */}
      <MemoryViewer />
    </div>
  );
};

export default MemoriesPage;
