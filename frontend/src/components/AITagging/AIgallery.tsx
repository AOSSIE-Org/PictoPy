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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

interface Image {
  id: string;
  url: string;
  tags: string[];
  imagePath: string;
  // Add other properties relevant to your images
}

interface QueryResponse {
  data: Image[];
  success: boolean;
  error?: string;
  message?: string;
}

export default function AIGallery({
  title,
  type,
  folderPath,
}: {
  title: string;
  type: 'image' | 'video';
  folderPath: string;
}) {
  const {
    data: mediaItemsData = { data: [], success: false },
    isLoading: loading,
    isError,
  } = usePictoQuery<QueryResponse>({
    queryFn: getAllImageObjects,
    queryKey: ['ai-tagging-images', 'ai'],
  });

  const { mutate: generateThumbnail, isPending: isCreating } = usePictoMutation({
    mutationFn: generateThumbnails,
    autoInvalidateTags: ['ai-tagging-images', 'ai'],
  });

  const [filterTag, setFilterTag] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const [isVisibleSelectedImage, setIsVisibleSelectedImage] = useState<boolean>(true);
  const itemsPerRow: number = 3;
  const noOfPages: number[] = Array.from({ length: 41 }, (_, index) => index + 10);
  const [pageNo, setPageNo] = useState<number>(20);

  // Filter media items based on the selected filter tags
  const filteredMediaItems = useMemo(() => {
    const mediaItems = mediaItemsData?.data ?? [];
    return filterTag.length > 0
      ? mediaItems.filter((mediaItem: Image) =>
          filterTag.some((tag) => mediaItem.tags.includes(tag))
        )
      : mediaItems;
  }, [filterTag, mediaItemsData]);

  // Paginate the filtered items
  const currentItems = useMemo(() => {
    const indexOfLastItem = currentPage * pageNo;
    const indexOfFirstItem = indexOfLastItem - pageNo;
    return filteredMediaItems.slice(indexOfFirstItem, indexOfLastItem);
  }, [filteredMediaItems, currentPage, pageNo]);

  const totalPages = Math.ceil(filteredMediaItems.length / pageNo);

  // Open the media viewer for the selected media item
  const openMediaViewer = useCallback((index: number) => {
    setSelectedMediaIndex(index);
    setShowMediaViewer(true);
  }, []);

  // Close the media viewer
  const closeMediaViewer = useCallback(() => {
    setShowMediaViewer(false);
  }, []);

  // Generate thumbnail when a folder is added
  const handleFolderAdded = useCallback(async () => {
    await generateThumbnail(folderPath);
  }, [folderPath, generateThumbnail]);

  // Effect to trigger the thumbnail generation when the folderPath changes
  useEffect(() => {
    handleFolderAdded();
  }, [folderPath, handleFolderAdded]);

  // Show loading screen if media items are being created or fetched
  if (isCreating || loading) {
    return <LoadingScreen />;
  }

  // Show error message if there is an issue fetching media items
  if (isError) {
    return <div>Error loading media items.</div>;
  }

  return (
    <div className="w-full">
      <div className="mx-auto px-2 pb-8 dark:bg-background dark:text-foreground">
        <div className="mb-2 flex items-center justify-between">
          {isVisibleSelectedImage && <h1 className="text-2xl font-bold">{title}</h1>}
          <FilterControls
            setFilterTag={setFilterTag}
            mediaItems={mediaItemsData.data}
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
            <div className="relative flex items-center justify-center gap-4">
              <PaginationControls
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
              />

              {/* Dropdown Menu - Right-Aligned */}
              <div className="absolute right-0 mt-5">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="flex items-center gap-2 border-gray-500 hover:bg-accent dark:hover:bg-white/10"
                    >
                      <p className="hidden lg:inline">
                        Num of images per page: {pageNo}
                      </p>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent
                    className="max-h-[500px] w-[200px] overflow-y-auto"
                    align="end"
                  >
                    <DropdownMenuRadioGroup
                      className="cursor-pointer overflow-auto bg-gray-950 p-4"
                      onValueChange={(value) => setPageNo(Number(value))}
                    >
                      {noOfPages.map((itemsPerPage) => (
                        <DropdownMenuRadioItem key={itemsPerPage} value={`${itemsPerPage}`}>
                          {itemsPerPage}
                        </DropdownMenuRadioItem>
                      ))}
                    </DropdownMenuRadioGroup>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </>
        )}

        {showMediaViewer && (
          <MediaView
            initialIndex={selectedMediaIndex}
            onClose={closeMediaViewer}
            allMedia={filteredMediaItems.map((item: Image) => ({
              url: item.url,
              path: item?.imagePath,
            }))}
            currentPage={currentPage}
            itemsPerPage={pageNo}
            type={type}
          />
        )}
      </div>
    </div>
  );
}
