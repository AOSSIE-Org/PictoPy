/**
 * FeaturedMemoryCard Component
 * 
 * Large, prominent card for "On This Day" section.
 * Shows hero image with "X years ago today" text overlay.
 */

import React from 'react';
import { MemoryImage } from '@/services/memoriesApi';
import { calculateYearsAgo, formatPhotoCount, getThumbnailUrl } from '@/services/memoriesApi';

interface FeaturedMemoryCardProps {
  images: MemoryImage[];
  today: string;
  years: number[];
  onClick: () => void;
}

/**
 * Featured memory card for "On This Day" section
 * Shows larger hero image with prominent styling
 */
export const FeaturedMemoryCard = React.memo<FeaturedMemoryCardProps>(({ images, years, onClick }) => {
  // Get the first image as hero
  const heroImage = images[0];
  
  if (!heroImage) return null;
  
  const thumbnailUrl = getThumbnailUrl(heroImage);
  
  // Calculate years ago from the captured date
  const yearsAgo = heroImage.captured_at ? calculateYearsAgo(heroImage.captured_at) : 0;
  
  // Handle image load error
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.src = '/placeholder-image.png';
  };

  return (
    <div
      onClick={onClick}
      className="group cursor-pointer bg-white dark:bg-gray-800 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden transform hover:scale-[1.01]"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      aria-label={`View On This Day memory from ${yearsAgo} years ago`}
    >
      <div className="relative">
        {/* Hero Image */}
        <div className="relative w-full h-64 md:h-96 lg:h-[28rem] bg-gradient-to-br from-blue-100 to-purple-100 dark:from-gray-700 dark:to-gray-800 overflow-hidden">
          <img
            src={thumbnailUrl}
            alt="On This Day"
            onError={handleImageError}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="eager"
          />
          
          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
          
          {/* Content Overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-6 md:p-8 text-white">
            {/* "On This Day" Badge */}
            <div className="inline-flex items-center bg-blue-500/90 backdrop-blur-sm px-3 py-1.5 rounded-full text-sm font-medium mb-3">
              <svg
                className="w-4 h-4 mr-2"
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
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-2 drop-shadow-lg">
              {yearsAgo === 1 ? 'On this day last year' : yearsAgo > 0 ? `${yearsAgo} years ago` : 'Today'}
            </h2>
            
            {/* Photo Count */}
            <div className="flex items-center text-sm md:text-base text-white/80">
              <svg
                className="w-5 h-5 mr-2"
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
              {years.length > 1 && ` from ${years.length} ${years.length === 1 ? 'year' : 'years'}`}
            </div>
          </div>
        </div>
        
        {/* Additional Images Preview (if more than 1) */}
        {images.length > 1 && (
          <div className="absolute top-4 right-4 flex -space-x-2">
            {images.slice(1, 4).map((img, idx) => (
              <div
                key={img.id}
                className="w-12 h-12 rounded-full border-2 border-white dark:border-gray-800 shadow-lg overflow-hidden bg-gray-200 dark:bg-gray-700"
                style={{ zIndex: 10 - idx }}
              >
                <img
                  src={getThumbnailUrl(img)}
                  alt=""
                  onError={handleImageError}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>
            ))}
            {images.length > 4 && (
              <div className="w-12 h-12 rounded-full border-2 border-white dark:border-gray-800 shadow-lg bg-black/60 backdrop-blur-sm flex items-center justify-center text-white text-xs font-bold">
                +{images.length - 4}
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* CTA Text */}
      <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800">
        <p className="text-center text-sm text-gray-600 dark:text-gray-400 font-medium group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
          Click to relive these memories →
        </p>
      </div>
    </div>
  );
});

FeaturedMemoryCard.displayName = 'FeaturedMemoryCard';

export default FeaturedMemoryCard;
