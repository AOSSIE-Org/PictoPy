import { useMemo, useState, useCallback } from 'react';
import MediaGrid from './Mediagrid';
import MediaView from './MediaView';
import SortingControls from './SortningControls';
import PaginationControls from '../ui/PaginationControls';
import { MediaGalleryProps } from '@/types/Media';
import { sortMedia } from '@/utils/Media';

export default function MediaGallery({
  mediaItems,
  title,
  type,
}: MediaGalleryProps) {
  const currentYear = new Date().getFullYear().toString();
  const [sortBy, setSortBy] = useState<string>('date');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const itemsPerPage: number = 20;
  const itemsPerRow: number = 3;

  const sortedMedia = useMemo(() => {
    return sortMedia(mediaItems, [sortBy]);
  }, [mediaItems, sortBy]);

  const currentItems = useMemo(() => {
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    return sortedMedia.slice(indexOfFirstItem, indexOfLastItem);
  }, [sortedMedia, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(sortedMedia.length / itemsPerPage);

  const handleSetSortBy = useCallback((value: string) => {
    setSortBy(value);
  }, []);

  const openMediaViewer = useCallback((index: number) => {
    setSelectedMediaIndex(index);
    setShowMediaViewer(true);
  }, []);

  const closeMediaViewer = useCallback(() => {
    setShowMediaViewer(false);
  }, []);
  return (
    <div className="w-full">
      <div className="mx-auto px-2 pb-8 pt-1 dark:bg-background dark:text-foreground">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-2xl font-bold">{title || currentYear}</h1>
          <SortingControls
            sortBy={sortBy}
            setSortBy={handleSetSortBy}
            mediaItems={mediaItems}
          />
        </div>
        <MediaGrid
          mediaItems={currentItems}
          itemsPerRow={itemsPerRow}
          openMediaViewer={openMediaViewer}
          type={type}
        />
        {totalPages >= 1 && (
          <PaginationControls
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        )}
        {showMediaViewer && (
          <MediaView
            initialIndex={selectedMediaIndex}
            onClose={closeMediaViewer}
            allMedia={sortedMedia.map((item) => {
              return { url: item.url, path: item?.imagePath };
            })}
            currentPage={currentPage}
            itemsPerPage={itemsPerPage}
            type={type}
          />
        )}
      </div>
    </div>
  );
}
