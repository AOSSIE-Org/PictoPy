import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Memory } from '@/types/Memory';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Calendar, MapPin, Images } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MemoryCardProps {
  memory: Memory;
  onClick: () => void;
}

export function MemoryCard({ memory, onClick }: MemoryCardProps) {
  const startDate = new Date(memory.date_range.start);
  const endDate = new Date(memory.date_range.end);

  // Format date range
  const formatDateRange = () => {
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    const shortOptions: Intl.DateTimeFormatOptions = {
      month: 'short',
      day: 'numeric',
    };

    if (memory.type === 'on_this_day') {
      return startDate.toLocaleDateString('en-US', options);
    }
    if (startDate.toDateString() === endDate.toDateString()) {
      return startDate.toLocaleDateString('en-US', options);
    }
    return `${startDate.toLocaleDateString('en-US', shortOptions)} - ${endDate.toLocaleDateString('en-US', options)}`;
  };

  // Get primary thumbnail (first one)
  const primaryThumbnail = memory.representative_media[0]?.thumbnailPath;

  return (
    <Card
      className={cn(
        'group cursor-pointer overflow-hidden transition-all hover:shadow-lg',
        'bg-card border',
      )}
      onClick={onClick}
    >
      {/* Image Grid Preview */}
      <div className="bg-muted relative h-48 w-full overflow-hidden">
        {primaryThumbnail ? (
          <div className="grid h-full grid-cols-3 grid-rows-2 gap-1">
            {memory.representative_media.slice(0, 6).map((media, idx) => (
              <div
                key={media.id}
                className={cn(
                  'relative overflow-hidden',
                  idx === 0 && 'col-span-2 row-span-2',
                )}
              >
                <img
                  src={convertFileSrc(media.thumbnailPath)}
                  alt={`Memory ${idx + 1}`}
                  className="h-full w-full object-cover transition-transform group-hover:scale-105"
                />
              </div>
            ))}
            {memory.representative_media.length < 6 && (
              <div className="flex items-center justify-center bg-black/20 text-white">
                <span className="text-xs font-medium">
                  +
                  {Math.max(
                    0,
                    memory.media_count - memory.representative_media.length,
                  )}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="flex h-full items-center justify-center">
            <Images className="text-muted-foreground h-12 w-12" />
          </div>
        )}

        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
      </div>

      <CardHeader className="pb-3">
        <CardTitle className="line-clamp-1 text-lg">{memory.title}</CardTitle>
        <CardDescription className="flex flex-col gap-1 text-xs">
          <div className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            <span>{formatDateRange()}</span>
          </div>
          {memory.location && (
            <div className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5" />
              <span className="line-clamp-1">{memory.location}</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 pt-1">
            <Images className="h-3.5 w-3.5" />
            <span>
              {memory.media_count}{' '}
              {memory.media_count === 1 ? 'photo' : 'photos'}
            </span>
          </div>
        </CardDescription>
      </CardHeader>
    </Card>
  );
}
