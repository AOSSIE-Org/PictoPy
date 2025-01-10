import { Check } from 'lucide-react';
import { MediaGridProps } from '@/types/Media';
import MediaCard from './MediaCard';

interface EnhancedMediaGridProps extends MediaGridProps {
  selectedImages?: Set<number>;
  onImageSelect?: (index: number) => void;
}

export default function MediaGrid({
  mediaItems,
  openMediaViewer,
  type,
  selectedImages = new Set(),
  onImageSelect,
}: EnhancedMediaGridProps) {
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

  const handleClick = (index: number, e: React.MouseEvent) => {
    if ((e.ctrlKey || e.metaKey) && onImageSelect) {
      onImageSelect(index);
      e.preventDefault(); // Prevent opening the media viewer when selecting
    } else {
      openMediaViewer(index);
    }
  };

  return (
    <div
      className={`grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4`}
    >
      {mediaItems.map((item, index) => (
        <div
          key={index}
          onClick={(e) => handleClick(index, e)}
          className="mt-4 cursor-pointer"
        >
          <div className="relative h-56">
            <MediaCard 
              item={item} 
              type={type} 
              className={selectedImages.has(index) ? 'brightness-75' : ''}
            />
            {selectedImages.has(index) && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                <Check className="h-8 w-8 text-white" />
              </div>
            )}
          </div>
          <p className="text-center text-sm font-medium">
            {getFileName(item.title || '')}
          </p>
        </div>
      ))}
    </div>
  );
}