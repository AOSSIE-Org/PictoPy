/**
 * MemoryCard Component
 * 
 * Displays a memory card with thumbnail, title, date, location, and photo count.
 * Used in grid layouts for Recent Memories, This Year, and All Memories sections.
 */

import React from 'react';
import { Memory } from '@/services/memoriesApi';
import { 
  formatDateRangeRelative, 
  formatPhotoCount, 
  getThumbnailUrl
} from '@/services/memoriesApi';

interface MemoryCardProps {
  memory: Memory;
  onClick: (memory: Memory) => void;
}

/**
 * Memory card component with hover effects and responsive design
 * SIMPLIFIED: Just show type badge, handle missing thumbnails, use convertFileSrc
 */
export const MemoryCard = React.memo<MemoryCardProps>(({ memory, onClick }) => {
  // Get thumbnail image (first image or find by thumbnail_image_id)
  const thumbnailImage = memory.images.find(img => img.id === memory.thumbnail_image_id) || memory.images[0];
  
  // Handle missing thumbnail gracefully - use path as fallback
  const thumbnailUrl = thumbnailImage 
    ? getThumbnailUrl(thumbnailImage) 
    : memory.images[0]?.path 
      ? getThumbnailUrl(memory.images[0])
      : '/photo.png';  // Default placeholder
  
  // Determine memory type
  const isDateBased = memory.center_lat === 0 && memory.center_lon === 0;
  
  // Format title based on memory type
  let displayTitle = memory.title || 'Untitled Memory';
  const displayLocation = memory.location_name || '';
  
  // For location-based memories, format as "Trip to [Location], [Year]"
  if (!isDateBased && displayLocation) {
    // Extract year from date_start
    const year = memory.date_start ? new Date(memory.date_start).getFullYear() : '';
    displayTitle = `Trip to ${displayLocation}${year ? `, ${year}` : ''}`;
  }
  
  // Handle image load error
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.src = '/photo.png';  // Fallback to default
  };

  return (
    <div
      onClick={() => onClick(memory)}
      className="group cursor-pointer bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-xl transition-all duration-200 overflow-hidden transform hover:scale-[1.02]"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(memory);
        }
      }}
      aria-label={`View memory: ${displayTitle}`}
    >
      {/* Thumbnail Image */}
      <div className="relative w-full h-48 bg-gray-200 dark:bg-gray-700 overflow-hidden">
        <img
          src={thumbnailUrl}
          alt={displayTitle}
          onError={handleImageError}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
          loading="lazy"
        />
        
        {/* Type Badge - Location or Date */}
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-black/70 text-white text-xs px-2 py-1 rounded-full backdrop-blur-sm">
          {isDateBased ? (
            <>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>Date</span>
            </>
          ) : (
            <>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Location</span>
            </>
          )}
        </div>
        
        {/* Photo Count Badge */}
        <div className="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded-full backdrop-blur-sm">
          {formatPhotoCount(memory.image_count)}
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4 space-y-2">
        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white line-clamp-1">
          {displayTitle}
        </h3>

        {/* Date Range - Relative Format */}
        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-1">
          {formatDateRangeRelative(memory.date_start, memory.date_end)}
        </p>

        {/* Location - Only show if not coordinates */}
        {displayLocation && (
          <div className="flex items-center text-sm text-gray-500 dark:text-gray-500">
            <svg
              className="w-4 h-4 mr-1 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span className="line-clamp-1">{displayLocation}</span>
          </div>
        )}

        {/* Description (optional, hidden on small screens) */}
        {memory.description && (
          <p className="hidden md:block text-xs text-gray-500 dark:text-gray-500 line-clamp-2 mt-2">
            {memory.description}
          </p>
        )}
      </div>
    </div>
  );
});

MemoryCard.displayName = 'MemoryCard';

export default MemoryCard;
