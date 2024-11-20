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
  const itemsPerPage: number = 9;
  const itemsPerRow: number = 3;

  const sortedMedia = useMemo(() => {
    return sortMedia(mediaItems, sortBy);
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
    <div className="container">
      <div className="mx-auto max-w-6xl px-4 py-8 dark:bg-background dark:text-foreground md:px-6">
        <div className="mb-6 flex items-center justify-between">
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
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
        {showMediaViewer && (
          <MediaView
            initialIndex={selectedMediaIndex}
            onClose={closeMediaViewer}
            allMedia={sortedMedia.map((item) => item.src)}
            currentPage={currentPage}
            itemsPerPage={itemsPerPage}
            type={type}
          />
        )}
      </div>
    </div>
  );
}
