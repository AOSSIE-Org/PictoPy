import React from 'react';

import { createImageErrorHandler } from '@/utils/imageFallback';
import { cn } from '@/lib/utils';
import type { MemoryCard } from '@/api/api-functions/memories';
import { MEMORY_PLACEHOLDER_IMAGE, getCoverUrl } from '@/utils/memories';

const handleCoverError = createImageErrorHandler(MEMORY_PLACEHOLDER_IMAGE);

interface MemoryFilmstripProps {
  memories: MemoryCard[];
  activeMemoryId: string | null;
  onSelect: (memoryId: string) => void;
}

/** Jumps between memories without leaving the story viewer. */
export const MemoryFilmstrip: React.FC<MemoryFilmstripProps> = ({
  memories,
  activeMemoryId,
  onSelect,
}) => {
  if (memories.length === 0) return null;

  return (
    <div
      role="tablist"
      aria-label="Past memories"
      className="hide-scrollbar flex gap-3 overflow-x-auto px-4 py-3"
    >
      {memories.map((memory) => {
        const isActive = memory.memory_id === activeMemoryId;
        return (
          <button
            key={memory.memory_id}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-label={memory.title}
            title={memory.title}
            onClick={() => onSelect(memory.memory_id)}
            className="focus-visible:ring-ring shrink-0 rounded-full focus-visible:ring-2 focus-visible:outline-none"
          >
            <span
              className={cn(
                'block rounded-full p-0.5 transition-colors',
                isActive
                  ? 'bg-white'
                  : memory.viewed_at === null
                    ? 'bg-primary'
                    : 'bg-white/25',
              )}
            >
              <img
                src={getCoverUrl(memory)}
                alt=""
                loading="lazy"
                onError={handleCoverError}
                className="h-14 w-14 rounded-full border-2 border-black/80 object-cover"
              />
            </span>
          </button>
        );
      })}
    </div>
  );
};

export default MemoryFilmstrip;
