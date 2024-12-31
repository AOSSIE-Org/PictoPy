// components/MediaGallery/MediaCard.tsx
import { MediaCardProps } from '@/types/Media';
import { Play } from 'lucide-react';

export default function MediaCard({ item, type }: MediaCardProps) {
  return (
    <div className="group relative h-full w-full overflow-hidden rounded-lg shadow-lg transition-transform duration-300 ease-in-out hover:-translate-y-2 hover:shadow-xl dark:bg-card dark:text-card-foreground">
      {type === 'image' ? (
        <img
          src={item.thumbnailUrl || item.url}
          alt={item.title}
          className="h-full w-full object-cover transition-opacity duration-300"
          style={{ opacity: 1 }}
        />
      ) : (
        <>
          <video
            src={item.url}
            className="h-full w-full object-cover transition-opacity duration-300"
            playsInline
            muted
          />
          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
            <Play
              className="h-12 w-12 text-white"
              fill="white"
              strokeWidth={1}
            />
          </div>
        </>
      )}
    </div>
  );
}
