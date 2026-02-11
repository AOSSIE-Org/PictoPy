/**
 * MemoryCard Component
 *
 * Displays a memory card with thumbnail, title, date, location, and photo count.
 * Used in grid layouts for Recent Memories, This Year, and All Memories sections.
 * Navigates to memory detail page on click.
 */

import React from 'react';
import { useNavigate } from 'react-router';
import { Memory } from '@/services/memoriesApi';
import {
  formatDateRangeRelative,
  formatPhotoCount,
  getThumbnailUrl,
} from '@/services/memoriesApi';

interface MemoryCardProps {
  memory: Memory;
}

/**
 * Memory card component with hover effects and responsive design
 * Navigates to detail page instead of using onClick callback
 */
export const MemoryCard = React.memo<MemoryCardProps>(({ memory }) => {
  const navigate = useNavigate();
  
  // Get thumbnail image (first image or find by thumbnail_image_id)
  const thumbnailImage =
    memory.images.find((img) => img.id === memory.thumbnail_image_id) ||
    memory.images[0];

  // Handle missing thumbnail gracefully - use path as fallback
  const thumbnailUrl = thumbnailImage
    ? getThumbnailUrl(thumbnailImage)
    : memory.images[0]?.path
      ? getThumbnailUrl(memory.images[0])
      : '/photo.png'; // Default placeholder

  // Determine memory type
  // Backend uses 0,0 as sentinel for date-based memories (no GPS data)
  const isDateBased = memory.center_lat == null || memory.center_lon == null;

  // Format title based on memory type
  let displayTitle = memory.title || 'Untitled Memory';
  const displayLocation = memory.location_name || '';

  // For location-based memories, format as "Trip to [Location], [Year]"
  if (!isDateBased && displayLocation) {
    // Extract year from date_start
    const year = memory.date_start
      ? new Date(memory.date_start).getFullYear()
      : '';
    displayTitle = `Trip to ${displayLocation}${year ? `, ${year}` : ''}`;
  }

  // Handle image load error
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.src = '/photo.png'; // Fallback to default
  };

  // Handle click - navigate to memory detail page
  const handleClick = () => {
    navigate(`/memories/${memory.memory_id}`);
  };

  return (
    <div
      onClick={handleClick}
      className="group transform cursor-pointer overflow-hidden rounded-lg border bg-card shadow-md transition-all duration-200 hover:scale-[1.02] hover:shadow-xl"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label={`View memory: ${displayTitle}`}
    >
      {/* Thumbnail Image */}
      <div className="relative h-48 w-full overflow-hidden bg-muted">
        <img
          src={thumbnailUrl}
          alt={displayTitle}
          onError={handleImageError}
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
          loading="lazy"
        />

        {/* Type Badge - Location or Date */}
        <div className="absolute top-2 left-2 flex items-center gap-1 rounded-full bg-black/70 px-2 py-1 text-xs text-white backdrop-blur-sm">
          {isDateBased ? (
            <>
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
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <span>Date</span>
            </>
          ) : (
            <>
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
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <span>Location</span>
            </>
          )}
        </div>

        {/* Photo Count Badge */}
        <div className="absolute top-2 right-2 rounded-full bg-black/70 px-2 py-1 text-xs text-white backdrop-blur-sm">
          {formatPhotoCount(memory.image_count)}
        </div>
      </div>

      {/* Card Content */}
      <div className="space-y-2 p-4">
        {/* Title */}
        <h3 className="line-clamp-1 text-lg font-semibold">
          {displayTitle}
        </h3>

        {/* Date Range - Relative Format */}
        <p className="line-clamp-1 text-sm text-muted-foreground">
          {formatDateRangeRelative(memory.date_start, memory.date_end)}
        </p>

        {/* Location - Only show if not coordinates */}
        {displayLocation && (
          <div className="flex items-center text-sm text-muted-foreground">
            <svg
              className="mr-1 h-4 w-4 shrink-0"
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
          <p className="mt-2 line-clamp-2 hidden text-xs text-gray-500 md:block dark:text-gray-500">
            {memory.description}
          </p>
        )}
      </div>
    </div>
  );
});

MemoryCard.displayName = 'MemoryCard';

export default MemoryCard;
