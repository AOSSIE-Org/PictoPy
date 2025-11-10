import { useState } from 'react';
import { Image } from '@/types/Media';
import { Calendar, Users, Tag, Clock } from 'lucide-react';
import { useDispatch } from 'react-redux';
import { setImages, setCurrentViewIndex } from '@/features/imageSlice';

interface MemoryCardProps {
  title: string;
  subtitle?: string;
  images: Image[];
  icon?: 'calendar' | 'users' | 'tag' | 'clock';
  imageCount?: number;
}

export const MemoryCard = ({
  title,
  subtitle,
  images,
  icon = 'calendar',
  imageCount,
}: MemoryCardProps) => {
  const dispatch = useDispatch();
  const [isExpanded, setIsExpanded] = useState(false);

  const displayImages = isExpanded ? images : images.slice(0, 6);
  const hasMore = images.length > 6;

  const iconMap = {
    calendar: Calendar,
    users: Users,
    tag: Tag,
    clock: Clock,
  };

  const Icon = iconMap[icon];

  const handleImageClick = (index: number) => {
    dispatch(setImages(images));
    dispatch(setCurrentViewIndex(index));
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-blue-100 p-2 dark:bg-blue-900">
            <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {title}
            </h3>
            {subtitle && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        {imageCount && (
          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-300">
            {imageCount} {imageCount === 1 ? 'photo' : 'photos'}
          </span>
        )}
      </div>

      {/* Image Grid */}
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6">
        {displayImages.map((image, index) => (
          <div
            key={image.id}
            className="group relative aspect-square cursor-pointer overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-700"
            onClick={() => handleImageClick(index)}
          >
            <img
              src={`picto-protocol://picto.image/${encodeURIComponent(image.thumbnailPath)}`}
              alt={image.metadata?.name || 'Memory'}
              className="h-full w-full object-cover transition-transform duration-200 group-hover:scale-110"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-black opacity-0 transition-opacity group-hover:opacity-10" />
          </div>
        ))}
      </div>

      {/* Show More/Less Button */}
      {hasMore && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-3 w-full rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
        >
          {isExpanded
            ? 'Show Less'
            : `Show ${images.length - 6} More ${images.length - 6 === 1 ? 'Photo' : 'Photos'}`}
        </button>
      )}
    </div>
  );
};
