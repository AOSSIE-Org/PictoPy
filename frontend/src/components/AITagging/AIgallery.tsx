import { useCallback, useEffect, useMemo, useState } from 'react';
import FilterControls from './FilterControls';
import MediaGrid from '../Media/Mediagrid';
import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import MediaView from '../Media/MediaView';
import PaginationControls from '../ui/PaginationControls';
import { usePictoQuery } from '@/hooks/useQueryExtensio';
import { getAllImageObjects } from '../../../api/api-functions/images';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import ProgressiveFolderLoader from '../ui/ProgressiveLoader';

import { UserSearch } from 'lucide-react';
import ErrorPage from '@/components/ui/ErrorPage/ErrorPage';

export default function AIGallery({
  title,
  type,
}: {
  title: string;
  type: 'image' | 'video';
}) {
  const {
    successData,
    error,
    isLoading: isGeneratingTags,
  } = usePictoQuery({
    queryFn: async () => await getAllImageObjects(),
    queryKey: ['ai-tagging-images', 'ai'],
  });
  const [addedFolders, setAddedFolders] = useState<string[]>([]);
  let mediaItems = successData ?? [];
  const [filterTag, setFilterTag] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const [isVisibleSelectedImage, setIsVisibleSelectedImage] =
    useState<boolean>(true);
  const [faceSearchResults, setFaceSearchResults] = useState<string[]>([]);

  const itemsPerRow: number = 3;
  const noOfPages: number[] = Array.from(
    { length: 41 },
    (_, index) => index + 10,
  );

  const filteredMediaItems = useMemo(() => {
    let filtered = mediaItems;
    if (faceSearchResults.length > 0) {
      filtered = filtered.filter((item: any) =>
        faceSearchResults.includes(item.imagePath),
      );
    }

    return filterTag.length > 0
      ? filtered.filter((mediaItem: any) =>
          filterTag.some((tag) => mediaItem.tags.includes(tag)),
        )
      : filtered;
  }, [filterTag, mediaItems, isGeneratingTags, faceSearchResults]);

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

  const handleFolderAdded = useCallback(async (newPaths: string[]) => {
    setAddedFolders(newPaths);
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [filterTag, faceSearchResults]);

  if (error) {
    return (
      <ErrorPage
        errorCode={500}
        errorMessage="Error loading media items."
        details="An unexpected error occurred while loading media items. This may be due to a server issue or database failure. Please try again later."
        onRetry={() => window.location.reload()}
      />
    );
  }

  return (
    <div className="w-full">
      <div className="dark:bg-background dark:text-foreground mx-auto px-2 pb-8">
        <div className="mb-2 flex items-center justify-between">
          {isVisibleSelectedImage && (
            <div className="flex items-center">
              <h1 className="text-2xl font-bold">{title}</h1>
              {faceSearchResults.length > 0 && (
                <div className="ml-4 flex items-center gap-2 rounded-lg bg-blue-100 px-3 py-1 dark:bg-blue-900/30">
                  <UserSearch size={16} />
                  <span className="text-sm">
                    Face filter active ({faceSearchResults.length} matches)
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={() => setFaceSearchResults([])}
                  >
                    ×
                  </Button>
                </div>
              )}
            </div>
          )}
          <FilterControls
            setFilterTag={setFilterTag}
            mediaItems={mediaItems}
            onFolderAdded={handleFolderAdded}
            isLoading={isGeneratingTags}
            isVisibleSelectedImage={isVisibleSelectedImage}
            setIsVisibleSelectedImage={setIsVisibleSelectedImage}
            setFaceSearchResults={setFaceSearchResults}
          />
          <ProgressiveFolderLoader
            additionalFolders={addedFolders}
            setAdditionalFolders={setAddedFolders}
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

              <div className="absolute right-0 mt-5">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="hover:bg-accent flex items-center gap-2 border-gray-500 dark:hover:bg-white/10"
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

        {isGeneratingTags ? (
          <LoadingScreen
            isLoading={isGeneratingTags}
            message="Generating tags..."
          />
        ) : (
          showMediaViewer && (
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
          )
        )}
      </div>
    </div>
  );
}
