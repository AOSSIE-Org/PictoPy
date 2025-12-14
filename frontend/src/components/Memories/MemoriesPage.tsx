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
  selectTotalMemoryCount
} from '@/store/slices/memoriesSlice';
import { MemoryCard } from './MemoryCard';
import { FeaturedMemoryCard } from './FeaturedMemoryCard';
import { MemoryViewer } from './MemoryViewer.tsx';
import type { Memory } from '@/services/memoriesApi';

/**
 * Loading skeleton for memory cards
 */
const MemoryCardSkeleton: React.FC = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden animate-pulse">
    <div className="w-full h-48 bg-gray-300 dark:bg-gray-700" />
    <div className="p-4 space-y-3">
      <div className="h-5 bg-gray-300 dark:bg-gray-700 rounded w-3/4" />
      <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
      <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-2/3" />
    </div>
  </div>
);

/**
 * Featured card skeleton for On This Day
 */
const FeaturedSkeleton: React.FC = () => (
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden animate-pulse">
    <div className="w-full h-64 md:h-96 lg:h-[28rem] bg-gradient-to-br from-gray-300 to-gray-400 dark:from-gray-700 dark:to-gray-800" />
    <div className="p-4 space-y-3">
      <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
    </div>
  </div>
);

/**
 * Section header component
 */
const SectionHeader: React.FC<{ title: string; count?: number }> = ({ title, count }) => (
  <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-6">
    {title}
    {count !== undefined && count > 0 && (
      <span className="ml-2 text-lg text-gray-500 dark:text-gray-400">({count})</span>
    )}
  </h2>
);

/**
 * Error message component with retry button
 */
const ErrorMessage: React.FC<{ message: string; onRetry: () => void }> = ({ message, onRetry }) => (
  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
    <div className="flex flex-col items-center space-y-3">
      <svg
        className="w-12 h-12 text-red-500 dark:text-red-400"
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
      <p className="text-red-800 dark:text-red-200 font-medium">{message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors duration-200"
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
  <div className="bg-gray-50 dark:bg-gray-800 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-12 text-center">
    <svg
      className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4"
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
    <p className="text-gray-600 dark:text-gray-400 text-lg">{message}</p>
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
  const locationCount = allMemories.filter(m => m.center_lat !== 0 || m.center_lon !== 0).length;
  const dateCount = allMemories.filter(m => m.center_lat === 0 && m.center_lon === 0).length;

  // Simple filter function
  const applyFilter = (memories: Memory[]) => {
    if (filter === 'location') {
      return memories.filter(m => m.center_lat !== 0 || m.center_lon !== 0);
    }
    if (filter === 'date') {
      return memories.filter(m => m.center_lat === 0 && m.center_lon === 0);
    }
    return memories;  // 'all'
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
        date_end: onThisDayImages[onThisDayImages.length - 1]?.captured_at || null,
        image_count: onThisDayImages.length,
        images: onThisDayImages,
        thumbnail_image_id: onThisDayImages[0]?.id || '',
        center_lat: onThisDayImages[0]?.latitude || 0,
        center_lon: onThisDayImages[0]?.longitude || 0
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
  const hasAnyData = onThisDayImages.length > 0 || recentMemories.length > 0 || 
                     yearMemories.length > 0 || allMemories.length > 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <svg
                className="w-8 h-8 text-blue-600 dark:text-blue-400"
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
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="Refresh memories"
            >
              <svg
                className="w-6 h-6"
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
        {/* Simple Filter Buttons */}
        {hasAnyData && (
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => setFilter('location')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === 'location'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Location ({locationCount})
            </button>
            <button
              onClick={() => setFilter('date')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === 'date'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
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
              <ErrorMessage message={error.onThisDay} onRetry={handleRetryOnThisDay} />
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
            <SectionHeader title="Recent Memories" count={filteredRecentMemories.length} />
            {loading.recent ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
                {[...Array(4)].map((_, i) => (
                  <MemoryCardSkeleton key={i} />
                ))}
              </div>
            ) : error.recent ? (
              <ErrorMessage message={error.recent} onRetry={handleRetryRecent} />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
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
            <SectionHeader title="This Year" count={filteredYearMemories.length} />
            {loading.year ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
                {[...Array(4)].map((_, i) => (
                  <MemoryCardSkeleton key={i} />
                ))}
              </div>
            ) : error.year ? (
              <ErrorMessage message={error.year} onRetry={handleRetryYear} />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
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
            <SectionHeader title="All Memories" count={filteredAllMemories.length} />
            {loading.all ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
                {[...Array(8)].map((_, i) => (
                  <MemoryCardSkeleton key={i} />
                ))}
              </div>
            ) : error.all ? (
              <ErrorMessage message={error.all} onRetry={handleRetryAll} />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
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
