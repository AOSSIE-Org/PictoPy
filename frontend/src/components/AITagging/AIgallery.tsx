import { useCallback, useMemo, useState } from 'react';
import FilterControls from './FilterControls';
import MediaGrid from '../Media/Mediagrid';

import { MediaGalleryProps } from '@/types/Media';
import MediaView from '../Media/MediaView';
import PaginationControls from '../ui/PaginationControls';
import { queryClient, usePictoQuery } from '@/hooks/useQueryExtensio';
import { getAllImageObjects } from '../../../api/api-functions/images';

export default function AIGallery({
  title,
  type,
  folderPath,
}: MediaGalleryProps & { folderPath: string }) {
  const { successData: mediaItems, isLoading: loading } = usePictoQuery({
    queryFn: getAllImageObjects,
    queryKey: ['ai-tagging-images', 'ai'],
  });

  const [filterTag, setFilterTag] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const [isVisibleSelectedImage, setIsVisibleSelectedImage] =
    useState<boolean>(true);
  const itemsPerPage: number = 20;


  const filteredMediaItems = useMemo(() => {
    return filterTag
      ? mediaItems.filter((mediaItem: any) =>
          mediaItem.tags.includes(filterTag),
        )
      : mediaItems;
  }, [filterTag, mediaItems, loading]);

  const currentItems = useMemo(() => {
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    return filteredMediaItems.slice(indexOfFirstItem, indexOfLastItem);
  }, [filteredMediaItems, currentPage, itemsPerPage, mediaItems]);

  const totalPages = Math.ceil(filteredMediaItems.length / itemsPerPage);

  const openMediaViewer = useCallback((index: number) => {
    setSelectedMediaIndex(index);
    setShowMediaViewer(true);
  }, []);

  const closeMediaViewer = useCallback(() => {
    setShowMediaViewer(false);
  }, []);

  const handleFolderAdded = useCallback(async () => {}, []);

  return (
    <div className="w-full">
      <div className="mx-auto px-2 pb-8 dark:bg-background dark:text-foreground">
        <div className="mb-6 flex items-center justify-between">
          {isVisibleSelectedImage && (
            <h1 className="text-2xl font-bold">{title}</h1>
          )}
          <FilterControls
            filterTag={filterTag}
            setFilterTag={setFilterTag}
            mediaItems={mediaItems}
            onFolderAdded={handleFolderAdded}
            isLoading={loading}
            isVisibleSelectedImage={isVisibleSelectedImage}
            setIsVisibleSelectedImage={setIsVisibleSelectedImage}
          />
        </div>

        {isVisibleSelectedImage && (
          <>
            <MediaGrid
              mediaItems={currentItems}
              
              openMediaViewer={openMediaViewer}
              type={type}
            />
            <PaginationControls
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          </>
        )}
        {showMediaViewer && (
          <MediaView
            initialIndex={selectedMediaIndex}
            onClose={closeMediaViewer}
            allMedia={filteredMediaItems.map((item: any) => item.src)}
            currentPage={currentPage}
            itemsPerPage={itemsPerPage}
            type={type}
          />
        )}
      </div>
    </div>
  );
}
