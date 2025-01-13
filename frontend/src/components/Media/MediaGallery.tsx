import { useMemo, useState, useCallback } from 'react';
import MediaGrid from './Mediagrid';
import MediaView from './MediaView';
import SortingControls from './SortningControls';
import PaginationControls from '../ui/PaginationControls';
import { MediaGalleryProps } from '@/types/Media';
import { sortMedia } from '@/utils/Media';
import { Input } from '@/components/ui/input';
import debounce from 'lodash/debounce';
import { Button } from '@/components/ui/button';

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
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const itemsPerPage: number = 20;
  const itemsPerRow: number = 3;

  const debouncedSearch = useMemo(
    () =>
      debounce(async (query: string) => {
        if (!query) {
          setIsSearching(false);
          return;
        }
        
        setIsSearching(true);
        try {
          const response = await fetch(`/api`);
          if (!response.ok) {
            throw new Error('Search failed');
          }
          const data = await response.json();
          console.log('Search results:', data);
          setIsSearching(false);
        } catch (error) {
          console.error('Search error:', error);
          setIsSearching(false);
        }
      }, 300),
    []
  );

  const handleSearchChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(event.target.value);
    },
    []
  );

  const handleSearchClick = useCallback(() => {
    setCurrentPage(1);
    debouncedSearch(searchQuery);
  }, [debouncedSearch, searchQuery]);

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
        <div className="mb-4 flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <h1 className="text-2xl font-bold">{title || currentYear}</h1>
          <div className="flex items-center space-x-4">
            <div className="relative w-full max-w-xs flex items-center space-x-2">
              <Input
                type="search"
                placeholder="Search media..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full"
                disabled={isSearching}
              />
              <Button onClick={handleSearchClick} disabled={isSearching}>
                Search
              </Button>
            </div>
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