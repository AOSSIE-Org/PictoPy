import { MediaGridProps } from '@/types/Media';
import MediaCard from './MediaCard';

export default function MediaGrid({
  mediaItems,
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

  const getFileName = (path: string) => {
    const fileName = path.split('\\').pop()?.split('/').pop() || path;
    const extension = fileName.split('.').pop();
    const baseName = fileName.replace(`.${extension}`, '');

    if (baseName.length > 15) {
      return `${baseName.slice(0, 15)}...${extension}`;
    }
    return fileName;
  };

  return (
    <div
      className={`grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4`}
    >
      {mediaItems.map((item, index) => (
        <div
          key={index}
          onClick={() => openMediaViewer(index)}
          className="mt-4 h-56 cursor-pointer"
        >
          <MediaCard item={item} type={type} />
          <p className="text-center text-sm font-medium">
            {getFileName(item.title || '')}
          </p>
        </div>
      ))}
    </div>
  );
}
