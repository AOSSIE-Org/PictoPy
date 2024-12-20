// components/MediaGallery/MediaCard.tsx

import { MediaCardProps } from '@/types/Media';

export default function MediaCard({ item, type }: MediaCardProps) {
  return (
    <div className="group relative h-full w-full overflow-hidden rounded-lg shadow-lg transition-transform duration-300 ease-in-out hover:-translate-y-2 hover:shadow-xl dark:bg-card dark:text-card-foreground">
      {type === 'image' ? (
        <img
          src={item.src}
          alt={item.title}
          className="h-full w-full object-cover transition-opacity duration-300"
          style={{ opacity: 1 }}
        />
      ) : (
        <video
          controls
          src={item.src}
          className="h-64 w-full object-cover transition-opacity duration-300"
        />
      )}
    </div>
  );
}
