import { AspectRatio } from '@/components/ui/aspect-ratio';
import { cn } from '@/lib/utils';
import { Play } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Video } from '@/types/Media';

interface VideoCardProps {
  video: Video;
  className?: string;
  onClick?: () => void;
}

export function VideoCard({ video, className, onClick }: VideoCardProps) {
  return (
    <div
      className={cn(
        'group bg-card cursor-pointer overflow-hidden rounded-lg border transition-all hover:shadow-md',
        className,
      )}
      onClick={onClick}
    >
      <div className="relative">
        <AspectRatio ratio={16 / 10}>
          <video
            src={convertFileSrc(video.path)}
            className="pointer-events-none h-full w-full object-cover transition-transform group-hover:scale-105"
            preload="metadata"
            muted
            playsInline
          />
          {/* Overlay with gradient */}
          <div className="absolute inset-0 flex flex-col justify-between bg-linear-to-t from-black/80 via-transparent to-black/40 p-3">
            {/* Video Badge */}
            <div className="inline-flex w-fit items-center rounded-full bg-black/60 px-2 py-1 text-xs font-medium text-white">
              Video
            </div>
            {/* Title */}
            <div className="line-clamp-2 font-medium text-white">
              {video.metadata?.name || video.title || 'Untitled'}
            </div>
          </div>
          {/* Play Button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="hover:bg-primary/80 rounded-full bg-black/40 p-4 backdrop-blur-sm transition-colors">
              <Play className="h-8 w-8 text-white" />
            </div>
          </div>
        </AspectRatio>
      </div>
    </div>
  );
}
