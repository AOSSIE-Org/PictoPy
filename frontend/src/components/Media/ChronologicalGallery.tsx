import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { Image } from '@/types/Media';
import { selectImages } from '@/features/imageSelectors';
import {
  groupImagesByYearMonthFromMetadata,
  createImageIndexMap,
} from '@/utils/dateUtils';

type ChronologicalGalleryProps = {
  images: Image[];
  showTitle?: boolean;
  title?: string;
  className?: string;
};

export const ChronologicalGallery = ({
  images,
  showTitle = false,
  title = 'Image Gallery',
  className = '',
}: ChronologicalGalleryProps) => {
  const allImages = useSelector(selectImages);

  // Optimized grouping with proper date handling
  const grouped = useMemo(
    () => groupImagesByYearMonthFromMetadata(images),
    [images],
  );

  // Optimized image index lookup
  const imageIndexMap = useMemo(
    () => createImageIndexMap(allImages),
    [allImages],
  );

  // Check if we have any images to display
  if (!images.length) {
    return (
      <div
        className={`flex h-64 items-center justify-center text-gray-500 ${className}`}
      >
        <div className="text-center">
          <div className="mb-2 text-2xl">📷</div>
          <div className="text-lg font-medium">No images found</div>
          <div className="text-sm">Upload some images to get started</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-0 ${className}`}>
      {/* Title */}
      {showTitle && (
        <div className="mb-6">
          <h1 className="text-2xl font-bold">{title}</h1>
        </div>
      )}

      {/* Gallery Content */}
      {Object.entries(grouped)
        .sort((a, b) => Number(b[0]) - Number(a[0])) // sort years descending (newest first)
        .map(([year, months]) => (
          <div key={year} data-year={year}>
            {Object.entries(months)
              .sort((a, b) => Number(b[0]) - Number(a[0])) // sort months descending (newest first)
              .map(([month, imgs]) => {
                const monthName = new Date(
                  Number(year),
                  Number(month) - 1,
                ).toLocaleString('default', { month: 'long' });

                return (
                  <div
                    key={`${year}-${month}`}
                    className="mb-8"
                    data-timeline-month={`${year}-${month}`}
                    id={`timeline-section-${year}-${month}`}
                  >
                    {/* Sticky Month/Year Header */}
                    <div className="bg-background sticky top-0 z-10 mb-4 py-3 backdrop-blur-sm">
                      <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                        {monthName} {year}
                      </h3>
                      <div className="mt-1 text-sm text-gray-500">
                        {imgs.length} {imgs.length === 1 ? 'image' : 'images'}
                      </div>
                    </div>

                    {/* Images Grid */}
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                      {imgs.map((img) => {
                        const reduxIndex = imageIndexMap.get(img.id) ?? -1;

                        return (
                          <div key={img.id} className="group relative">
                            <ImageCard
                              image={img}
                              imageIndex={reduxIndex}
                              className="w-full transition-transform duration-200 group-hover:scale-105"
                            />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
          </div>
        ))}
    </div>
  );
};
