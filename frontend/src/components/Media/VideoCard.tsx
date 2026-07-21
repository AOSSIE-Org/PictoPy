import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Film, Heart, Play } from 'lucide-react';
import type React from 'react';
import { useCallback } from 'react';
import { Video } from '@/types/Media';
import { convertFileSrc } from '@tauri-apps/api/core';
import { useToggleVideoFav } from '@/hooks/useToggleVideoFav';
import { formatDurationLabel } from '@/utils/durationUtils';

interface VideoCardProps {
  video: Video;
  className?: string;
  onClick?: () => void;
}

export function VideoCard({ video, className, onClick }: VideoCardProps) {
  const { toggleFavourite, toggleFavouritePending } = useToggleVideoFav();
  const duration = formatDurationLabel(video.metadata?.duration);

  const handleToggleFavourite = useCallback(() => {
    if (video?.id && !toggleFavouritePending) {
      toggleFavourite(video.id);
    }
  }, [video, toggleFavourite, toggleFavouritePending]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      // Ignore keys aimed at the favourite button nested inside the card.
      if (e.target !== e.currentTarget) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onClick?.();
      }
    },
    [onClick],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Play ${video.metadata?.name || 'video'}`}
      className={cn(
        'group bg-card focus-visible:ring-primary cursor-pointer overflow-hidden rounded-lg border transition-all hover:shadow-md focus-visible:ring-2 focus-visible:outline-none',
        className,
      )}
      onClick={onClick}
      onKeyDown={handleKeyDown}
    >
      <div className="relative">
        <AspectRatio ratio={1}>
          {video.thumbnailPath ? (
            <img
              src={convertFileSrc(video.thumbnailPath)}
              alt={video.metadata?.name || 'Video thumbnail'}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <div className="bg-muted flex h-full w-full items-center justify-center">
              <Film className="text-muted-foreground h-10 w-10" />
            </div>
          )}
          {/* Dark overlay on hover */}
          <div className="absolute inset-0 bg-black/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />

          {/* Centered play indicator */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="rounded-full bg-black/50 p-3 text-white transition-transform duration-200 group-hover:scale-110">
              <Play className="h-6 w-6" fill="currentColor" />
            </div>
          </div>

          {/* Favourite action: revealed on hover, or on keyboard focus */}
          <div className="absolute top-2 right-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100 focus-within:opacity-100">
            <Button
              variant="ghost"
              size="icon"
              disabled={toggleFavouritePending}
              aria-busy={toggleFavouritePending}
              className={`cursor-pointer rounded-full p-2.5 text-white transition-all duration-300 ${
                video.isFavourite
                  ? 'bg-rose-500/80 hover:bg-rose-600 hover:shadow-lg'
                  : 'bg-white/10 hover:bg-white/20 hover:shadow-lg'
              }`}
              onClick={(e) => {
                e.stopPropagation();
                handleToggleFavourite();
              }}
            >
              {video.isFavourite ? (
                <Heart className="h-5 w-5" fill="currentColor" />
              ) : (
                <Heart className="h-5 w-5" />
              )}
              <span className="sr-only">Favourite</span>
            </Button>
          </div>

          {/* Duration badge */}
          {duration && (
            <div className="absolute right-2 bottom-2 rounded bg-black/70 px-1.5 py-0.5 text-xs font-medium text-white">
              {duration}
            </div>
          )}
        </AspectRatio>
      </div>
    </div>
  );
}
