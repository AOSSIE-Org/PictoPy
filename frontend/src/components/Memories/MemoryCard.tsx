import React from 'react';
import { FolderPlus, Images, MoreVertical } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { createImageErrorHandler } from '@/utils/imageFallback';
import type { MemoryCard as MemoryCardType } from '@/api/api-functions/memories';
import {
  MEMORY_PLACEHOLDER_IMAGE,
  formatEventType,
  formatMemorySubtitle,
  formatPhotoCount,
  getCoverUrl,
} from '@/utils/memories';

const handleCoverError = createImageErrorHandler(MEMORY_PLACEHOLDER_IMAGE);

interface MemoryCardProps {
  memory: MemoryCardType;
  onOpen: (memoryId: string) => void;
  onConvertToAlbum: (memoryId: string) => void;
}

/**
 * Grid tile for one memory. The cover scales and the caption lifts on hover;
 * the tile opens the story viewer, and the actions menu sits beside it rather
 * than inside it - a button cannot contain another button.
 */
export const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  onOpen,
  onConvertToAlbum,
}) => {
  const subtitle = formatMemorySubtitle(memory);
  const isUnviewed = memory.viewed_at === null;

  return (
    <div className="group relative aspect-4/5 w-full">
      <button
        type="button"
        onClick={() => onOpen(memory.memory_id)}
        aria-label={`Open memory: ${memory.title}`}
        className="focus-visible:ring-ring relative h-full w-full overflow-hidden rounded-xl text-left focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none"
      >
        <img
          src={getCoverUrl(memory)}
          alt=""
          loading="lazy"
          onError={handleCoverError}
          className="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-105"
        />

        {/* Scrim: keeps the caption legible over an arbitrary photo. */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

        <div className="absolute top-3 left-3 flex items-center gap-2">
          <Badge
            variant="secondary"
            className="bg-black/50 text-white backdrop-blur-sm"
          >
            {formatEventType(memory.event_type)}
          </Badge>
          {isUnviewed && (
            <span
              aria-label="Not yet viewed"
              className="bg-primary h-2 w-2 rounded-full ring-2 ring-black/40"
            />
          )}
        </div>

        <div className="absolute right-3 bottom-3 left-3 translate-y-1 transition-transform duration-300 ease-out group-hover:translate-y-0">
          <h3 className="line-clamp-2 text-base font-semibold text-white">
            {memory.title}
          </h3>
          {subtitle && (
            <p className="mt-0.5 line-clamp-1 text-sm text-white/75">
              {subtitle}
            </p>
          )}
          <p className="mt-1.5 flex items-center gap-1.5 text-xs text-white/60">
            <Images className="h-3.5 w-3.5" aria-hidden />
            {formatPhotoCount(memory.image_count)}
          </p>
        </div>
      </button>

      {/* Actions menu, matching the album grid's affordance. */}
      <div className="absolute top-3 right-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              aria-label={`Options for ${memory.title}`}
              className="bg-background/80 hover:bg-background/90 h-9 w-9 rounded-full backdrop-blur-sm"
            >
              <MoreVertical className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem
              onClick={() => onConvertToAlbum(memory.memory_id)}
            >
              <FolderPlus className="mr-2 h-4 w-4" />
              Convert to Album
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

export default MemoryCard;
