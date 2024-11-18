// components/MediaGallery/MediaGrid.tsx
import { MediaGridProps } from '@/types/Media';
import MediaCard from './MediaCard';

export default function MediaGrid({
  mediaItems,
  itemsPerRow,
  openMediaViewer,
  type,
}: MediaGridProps) {
  if (mediaItems.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center">
        <h1 className="text-2xl font-bold">No media found</h1>
      </div>
    );
  }
  return (
    <div
      className={`grid gap-4 md:gap-6 ${
        itemsPerRow === 2
          ? 'grid-cols-1 sm:grid-cols-2'
          : itemsPerRow === 3
            ? 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3'
            : 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
      }`}
    >
      {mediaItems.map((item, index) => (
        <div
          key={index}
          onClick={() => openMediaViewer(index)}
          className="cursor-pointer"
        >
          <MediaCard item={item} type={type} />
        </div>
      ))}
    </div>
  );
}
