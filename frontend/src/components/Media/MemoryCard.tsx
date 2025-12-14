// src/components/Media/MemoryCard.tsx

import { MemorySummary } from '@/types/Memory';
import { Calendar, MapPin, Images } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/core';

interface MemoryCardProps {
  memory: MemorySummary;
  onClick: () => void;
}

export const MemoryCard = ({ memory, onClick }: MemoryCardProps) => {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getMemoryTypeDisplay = (type: string) => {
    const typeMap: Record<string, string> = {
      on_this_day: 'On This Day',
      trip: 'Trip',
      location: 'Location',
      month_highlight: 'Monthly Highlight',
    };
    return typeMap[type] || type;
  };

  // Get representative images (max 4 for grid display)
  const displayImages = memory.representative_thumbnails.slice(0, 4);
  const remainingCount = memory.total_photos - displayImages.length;

  return (
    <div
      onClick={onClick}
      className="group relative cursor-pointer overflow-hidden rounded-lg bg-card shadow-md transition-all duration-300 hover:scale-[1.02] hover:shadow-xl"
    >
      {/* Image Grid */}
      <div className="relative aspect-square w-full overflow-hidden bg-muted">
        {displayImages.length === 1 ? (
          // Single image
          <img
            src={convertFileSrc(displayImages[0])}
            alt={memory.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
          />
        ) : (
          // Grid of images
          <div className="grid h-full w-full grid-cols-2 gap-1">
            {displayImages.map((thumbnail, idx) => (
              <div key={idx} className="relative overflow-hidden">
                <img
                  src={convertFileSrc(thumbnail)}
                  alt={`${memory.title} ${idx + 1}`}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                />
              </div>
            ))}
            {/* Show remaining count if more than 4 images */}
            {remainingCount > 0 && displayImages.length === 4 && (
              <div className="absolute bottom-2 right-2 rounded-full bg-black/70 px-3 py-1 text-xs font-medium text-white">
                +{remainingCount}
              </div>
            )}
          </div>
        )}

        {/* Memory type badge */}
        <div className="absolute left-2 top-2 rounded-full bg-black/60 px-3 py-1 text-xs font-medium text-white backdrop-blur-sm">
          {getMemoryTypeDisplay(memory.memory_type)}
        </div>

        {/* Overlay gradient */}
        <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 to-transparent" />
      </div>

      {/* Memory Info */}
      <div className="absolute inset-x-0 bottom-0 p-4 text-white">
        <h3 className="mb-2 line-clamp-2 text-lg font-semibold drop-shadow-lg">
          {memory.title}
        </h3>

        <div className="flex flex-wrap items-center gap-3 text-sm">
          {/* Date */}
          <div className="flex items-center gap-1 opacity-90">
            <Calendar className="h-4 w-4" />
            <span>{formatDate(memory.start_date)}</span>
          </div>

          {/* Location */}
          {memory.location && (
            <div className="flex items-center gap-1 opacity-90">
              <MapPin className="h-4 w-4" />
              <span className="line-clamp-1">{memory.location}</span>
            </div>
          )}

          {/* Photo count */}
          <div className="flex items-center gap-1 opacity-90">
            <Images className="h-4 w-4" />
            <span>{memory.total_photos} photos</span>
          </div>
        </div>
      </div>
    </div>
  );
};