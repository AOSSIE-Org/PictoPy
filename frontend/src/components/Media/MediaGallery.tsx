import { useMemo, useState, useCallback } from 'react';
import MediaGrid from './Mediagrid';
import MediaView from './MediaView';
import SortingControls from './SortningControls';
import PaginationControls from '../ui/PaginationControls';
import { MediaGalleryProps } from '@/types/Media';
import { sortMedia } from '@/utils/Media';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@radix-ui/react-dropdown-menu';
import { Button } from '../ui/button';

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

  const noOfPages: number[] = Array.from(
    { length: 41 },
    (_, index) => index + 10,
  );
  const [pageNo, setpageNo] = useState<number>(20);
  const sortedMedia = useMemo(() => {
    return sortMedia(mediaItems, [sortBy]);
  }, [mediaItems, sortBy]);

  const currentItems = useMemo(() => {
    const indexOfLastItem = currentPage * pageNo;
    const indexOfFirstItem = indexOfLastItem - pageNo;
    return sortedMedia.slice(indexOfFirstItem, indexOfLastItem);
  }, [sortedMedia, currentPage, pageNo]);

  const totalPages = Math.ceil(sortedMedia.length / pageNo);

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
          <div className='relative flex items-center justify-center gap-4'>
            <PaginationControls
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
            <div className="absolute right-0 mt-5">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    className="flex items-center gap-2 border-gray-500 hover:bg-accent dark:hover:bg-white/10"
                  >
                    <p className="hidden lg:inline">
                      Num of images per page : {pageNo}
                    </p>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="max-h-[500px] w-[200px] overflow-y-auto"
                  align="end"
                >
                  <DropdownMenuRadioGroup
                    className="cursor-pointer overflow-auto bg-gray-950 p-4"
                    onValueChange={(value) => setpageNo(Number(value))}
                  >
                    {noOfPages.map((itemsPerPage) => (
                      <DropdownMenuRadioItem
                        key={itemsPerPage}
                        value={`${itemsPerPage}`}
                      >
                        {itemsPerPage}
                      </DropdownMenuRadioItem>
                    ))}
                  </DropdownMenuRadioGroup>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        )}
        {showMediaViewer && (
          <MediaView
            initialIndex={selectedMediaIndex}
            onClose={closeMediaViewer}
            allMedia={sortedMedia.map((item) => item.url)}
            currentPage={currentPage}
            itemsPerPage={itemsPerPage}
            type={type}
          />
        )}
      </div>
    </div>
  );
}
