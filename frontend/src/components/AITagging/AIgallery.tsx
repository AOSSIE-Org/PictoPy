import { useCallback, useEffect, useMemo, useState } from 'react';
import FilterControls from './FilterControls';
import MediaGrid from '../Media/Mediagrid';

import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import MediaView from '../Media/MediaView';
import PaginationControls from '../ui/PaginationControls';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtensio';
import {
  getAllImageObjects,
  generateThumbnails,
} from '../../../api/api-functions/images';

export default function AIGallery({
  title,
  type,
  folderPath,
}: {
  title: string;
  type: 'image' | 'video';
  folderPath: string;
}) {
  const { successData, isLoading: loading } = usePictoQuery({
    queryFn: async () => await getAllImageObjects(),
    queryKey: ['ai-tagging-images', 'ai'],
  });
  const { mutate: generateThumbnail, isPending: isCreating } = usePictoMutation(
    {
      mutationFn: generateThumbnails,
      autoInvalidateTags: ['ai-tagging-images', 'ai'],
    },
  );
  let mediaItems = successData ?? [];
  const [filterTag, setFilterTag] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const [isVisibleSelectedImage, setIsVisibleSelectedImage] =
    useState<boolean>(true);
  const itemsPerPage: number = 20;
  const itemsPerRow: number = 3;

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

  const handleFolderAdded = useCallback(async () => {
    generateThumbnail(folderPath);
  }, []);

  useEffect(() => {
    generateThumbnail(folderPath);
  }, [folderPath]);

  if (isCreating || loading) {
    return (
      <div>
        <LoadingScreen />
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mx-auto px-2 pb-8 dark:bg-background dark:text-foreground">
        <div className="mb-2 flex items-center justify-between">
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
              itemsPerRow={itemsPerRow}
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
            allMedia={filteredMediaItems.map((item: any) => item.url)}
            currentPage={currentPage}
            itemsPerPage={itemsPerPage}
            type={type}
          />
        )}
      </div>
    </div>
  );
}
