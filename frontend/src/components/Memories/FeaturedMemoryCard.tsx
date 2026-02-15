/**
 * FeaturedMemoryCard Component
 *
 * Large, prominent card for "On This Day" section.
 * Shows hero image with "X years ago today" text overlay.
 * Navigates to memory detail page on click.
 */

import React from 'react';
import { useNavigate } from 'react-router';
import { MemoryImage } from '@/services/memoriesApi';
import {
  calculateYearsAgo,
  formatPhotoCount,
  getThumbnailUrl,
} from '@/services/memoriesApi';

interface FeaturedMemoryCardProps {
  images: MemoryImage[];
  today: string;
  years: number[];
  memoryId: string;
}

/**
 * Featured memory card for "On This Day" section
 * Shows larger hero image with prominent styling
 */
export const FeaturedMemoryCard = React.memo<FeaturedMemoryCardProps>(
  ({ images, years, memoryId }) => {
    const navigate = useNavigate();

    // Get the first image as hero
    const heroImage = images[0];

    if (!heroImage) return null;

    const thumbnailUrl = getThumbnailUrl(heroImage);

    // Calculate years ago from the captured date
    const yearsAgo = heroImage.captured_at
      ? calculateYearsAgo(heroImage.captured_at)
      : 0;

    // Handle image load error
    const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
      e.currentTarget.src = '/photo.png';
    };

    // Handle click - navigate to memory detail page
    const handleClick = () => {
      navigate(`/memories/${memoryId}`);
    };

    return (
      <div
        onClick={handleClick}
        className="group bg-card transform cursor-pointer overflow-hidden rounded-xl border shadow-lg transition-all duration-300 hover:scale-[1.01] hover:shadow-2xl"
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
        aria-label={`View On This Day memory from ${yearsAgo} years ago`}
      >
        <div className="relative">
          {/* Hero Image */}
          <div className="bg-muted relative h-64 w-full overflow-hidden md:h-96 lg:h-[28rem]">
            <img
              src={thumbnailUrl}
              alt="On This Day"
              onError={handleImageError}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="eager"
            />

            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />

            {/* Content Overlay */}
            <div className="absolute right-0 bottom-0 left-0 p-6 text-white md:p-8">
              {/* "On This Day" Badge */}
              <div className="mb-3 inline-flex items-center rounded-full bg-blue-500/90 px-3 py-1.5 text-sm font-medium backdrop-blur-sm">
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                On This Day
              </div>

              {/* Years Ago Text */}
              <h2 className="mb-2 text-3xl font-bold drop-shadow-lg md:text-4xl lg:text-5xl">
                {yearsAgo === 1
                  ? 'On this day last year'
                  : yearsAgo > 0
                    ? `${yearsAgo} years ago`
                    : 'Today'}
              </h2>

              {/* Photo Count */}
              <div className="flex items-center text-sm text-white/80 md:text-base">
                <svg
                  className="mr-2 h-5 w-5"
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
                {formatPhotoCount(images.length)}
                {years.length > 1 &&
                  ` from ${years.length} ${years.length === 1 ? 'year' : 'years'}`}
              </div>
            </div>
          </div>

          {/* Additional Images Preview (if more than 1) */}
          {images.length > 1 && (
            <div className="absolute top-4 right-4 flex -space-x-2">
              {images.slice(1, 4).map((img, idx) => (
                <div
                  key={img.id}
                  className="h-12 w-12 overflow-hidden rounded-full border-2 border-white bg-gray-200 shadow-lg dark:border-gray-800 dark:bg-gray-700"
                  style={{ zIndex: 10 - idx }}
                >
                  <img
                    src={getThumbnailUrl(img)}
                    alt=""
                    onError={handleImageError}
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                </div>
              ))}
              {images.length > 4 && (
                <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-white bg-black/60 text-xs font-bold text-white shadow-lg backdrop-blur-sm dark:border-gray-800">
                  +{images.length - 4}
                </div>
              )}
            </div>
          )}
        </div>

        {/* CTA Text */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 dark:from-gray-800 dark:to-gray-800">
          <p className="text-center text-sm font-medium text-gray-600 transition-colors group-hover:text-blue-600 dark:text-gray-400 dark:group-hover:text-blue-400">
            Click to relive these memories →
          </p>
        </div>
      </div>
    );
  },
);

FeaturedMemoryCard.displayName = 'FeaturedMemoryCard';

export default FeaturedMemoryCard;
