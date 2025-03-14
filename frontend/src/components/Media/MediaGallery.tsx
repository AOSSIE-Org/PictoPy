import { useMemo, useState, useCallback } from 'react';
import MediaGrid from './Mediagrid';
import MediaView from './MediaView';
import SortingControls from './SortningControls';
import PaginationControls from '../ui/PaginationControls';
import { MediaGalleryProps } from '@/types/Media';
import { sortMedia } from '@/utils/Media';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import { deleteCache } from '@/services/cacheService';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@radix-ui/react-dropdown-menu';

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

  const handleRefreshClick = async () => {
    try {
      const result = await deleteCache();
      if (result) {
        console.log('Cache deleted');
      }
      window.location.reload();
    } catch (error) {
      console.error('Error deleting cache:', error);
    }
  };

  return (
    <div className="container mx-auto w-full max-w-7xl px-4">
      <div className="mx-auto px-0 pb-12 pt-3 dark:bg-background dark:text-foreground md:px-2">
        <div className="mb-6 flex flex-col gap-4 border-b pb-4 dark:border-gray-800 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-2xl font-bold text-transparent dark:from-gray-100 dark:to-gray-300 sm:text-3xl">
            {title || currentYear}
          </h1>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={() => handleRefreshClick()}
              variant="outline"
              className="border-gray-200/80 bg-white/90 shadow-sm transition-all duration-200 hover:bg-gray-50/90 hover:shadow-md dark:border-gray-800/80 dark:bg-gray-800/80 dark:text-gray-100 dark:hover:bg-gray-700/90 dark:hover:text-white"
            >
              <RefreshCw className="mr-2 h-4 w-4 text-gray-500 dark:text-gray-400" />
              <span className="hidden text-sm md:inline">Refresh</span>
            </Button>
            <SortingControls
              sortBy={sortBy}
              setSortBy={handleSetSortBy}
              mediaItems={mediaItems}
            />
          </div>
        </div>

        <MediaGrid
          mediaItems={currentItems}
          itemsPerRow={itemsPerRow}
          openMediaViewer={openMediaViewer}
          type={type}
        />

        {totalPages >= 1 && (
          <div className="mt-8 flex flex-col items-center justify-between gap-4 sm:flex-row">
            <PaginationControls
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />

            <div className="mt-4 sm:mt-0">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    className="border-gray-200/80 bg-white/90 shadow-sm transition-all duration-200 hover:bg-gray-50/90 hover:shadow-md dark:border-gray-800/80 dark:bg-gray-800/80 dark:text-gray-100 dark:hover:bg-gray-700/90 dark:hover:text-white"
                  >
                    <span className="max-w-[180px] truncate text-sm">
                      {pageNo} images per page
                    </span>
                  </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent
                  className="rounded-xl max-h-[500px] w-[200px] overflow-y-auto border border-gray-200/80 bg-white/95 shadow-lg backdrop-blur-sm dark:border-gray-800/80 dark:bg-gray-800/95"
                  align="end"
                  sideOffset={5}
                >
                  <DropdownMenuRadioGroup
                    className="p-1.5"
                    onValueChange={(value) => setpageNo(Number(value))}
                  >
                    {noOfPages.map((itemsPerPage) => (
                      <DropdownMenuRadioItem
                        key={itemsPerPage}
                        value={`${itemsPerPage}`}
                        className="cursor-pointer rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors hover:bg-gray-100/80 dark:hover:bg-gray-700/80"
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
            allMedia={sortedMedia.map((item) => {
              return {
                url: item.url,
                path: item?.imagePath,
                thumbnailUrl: item.thumbnailUrl,
              };
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
