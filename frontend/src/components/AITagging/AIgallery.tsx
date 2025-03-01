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
import ProgressiveFolderLoader from '../ui/ProgressiveLoader';

export default function AIGallery({
  title,
  type,
  folderPath,
}: {
  title: string;
  type: 'image' | 'video';
  folderPath: string;
}) {
  const { successData, isLoading: isGeneratingTags } = usePictoQuery({
    queryFn: async () => await getAllImageObjects(),
    queryKey: ['ai-tagging-images', 'ai'],
  });
  const { mutate: generateThumbnailAPI } =
    usePictoMutation({
      mutationFn: generateThumbnails,
      autoInvalidateTags: ['ai-tagging-images', 'ai'],
    });
  const [addedFolders, setAddedFolders] = useState<string[]>([]);
  let mediaItems = successData ?? [];
  const [filterTag, setFilterTag] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const [isVisibleSelectedImage, setIsVisibleSelectedImage] =
    useState<boolean>(true);
  const itemsPerRow: number = 3;
  const noOfPages: number[] = Array.from(
    { length: 41 },
    (_, index) => index + 10,
  );
  const filteredMediaItems = useMemo(() => {
    return filterTag.length > 0
      ? mediaItems.filter((mediaItem: any) =>
          filterTag.some((tag) => mediaItem.tags.includes(tag)),
        )
      : mediaItems;
  }, [filterTag, mediaItems, isGeneratingTags]);

  const [pageNo, setpageNo] = useState<number>(20);

  const currentItems = useMemo(() => {
    const indexOfLastItem = currentPage * pageNo;
    const indexOfFirstItem = indexOfLastItem - pageNo;
    return filteredMediaItems.slice(indexOfFirstItem, indexOfLastItem);
  }, [filteredMediaItems, currentPage, pageNo]);

  const totalPages = Math.ceil(filteredMediaItems.length / pageNo);

  const openMediaViewer = useCallback((index: number) => {
    setSelectedMediaIndex(index);
    setShowMediaViewer(true);
  }, []);

  const closeMediaViewer = useCallback(() => {
    setShowMediaViewer(false);
  }, []);

  const handleFolderAdded = useCallback(async (newPaths:string[]) => {
    generateThumbnailAPI([folderPath, ...newPaths]);
    setAddedFolders(newPaths);
  }, []);

  useEffect(() => {
    generateThumbnailAPI([folderPath]);
  }, [folderPath]);

  if (isGeneratingTags) {
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
            setFilterTag={setFilterTag}
            mediaItems={mediaItems}
            onFolderAdded={handleFolderAdded}
            isLoading={isGeneratingTags}
            isVisibleSelectedImage={isVisibleSelectedImage}
            setIsVisibleSelectedImage={setIsVisibleSelectedImage}
          />
          <ProgressiveFolderLoader additionalFolders={addedFolders} />
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
          </>
        )}

        {showMediaViewer && (
          <MediaView
            initialIndex={selectedMediaIndex}
            onClose={closeMediaViewer}
            allMedia={filteredMediaItems.map((item: any) => ({
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
