import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { MediaView } from '@/components/Media/MediaView';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { ImageCard } from '@/components/Media/ImageCard';
import { FolderOpen, Image as ImageIcon } from 'lucide-react';

export const Home = () => {
  const dispatch = useDispatch();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);

  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;
  const searchResults = searchState.images;

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
    enabled: !isSearchActive,
  });

  // Handle fetching lifecycle
  useEffect(() => {
    if (!isSearchActive) {
      if (isLoading) {
        dispatch(showLoader('Loading images'));
      } else if (isError) {
        dispatch(hideLoader());
        dispatch(
          showInfoDialog({
            title: 'Error',
            message: 'Failed to load images. Please try again later.',
            variant: 'error',
          }),
        );
      } else if (isSuccess) {
        const images = data?.data as Image[];
        dispatch(setImages(images));
        dispatch(hideLoader());
      }
    }
  }, [data, isSuccess, isError, isLoading, dispatch, isSearchActive]);

  const handleCloseMediaView = () => {
    // MediaView will handle closing via Redux
  };

  const displayImages = isSearchActive ? searchResults : images;

  const title =
    isSearchActive && searchResults.length > 0
      ? `Face Search Results (${searchResults.length} found)`
      : 'Image Gallery';

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold">{title}</h1>

      {/* Empty State Placeholder */}
      {displayImages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
            <FolderOpen className="h-16 w-16 text-gray-400" />
          </div>
          <h2 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
            No Images to Display
          </h2>
          <p className="mb-6 max-w-md text-gray-500 dark:text-gray-400">
            Your gallery is empty. Please add a folder containing images to get
            started.
          </p>
          <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
            <div className="flex items-center gap-2">
              <ImageIcon className="h-4 w-4" />
              <span>Supported formats: PNG, JPG, JPEG, GIF, BMP</span>
            </div>
            <div className="flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              <span>Go to Settings to add folders</span>
            </div>
          </div>
        </div>
      )}

      {/* Image Grid */}
      {displayImages.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {displayImages.map((image, index) => (
            <ImageCard
              key={image.id}
              image={image}
              imageIndex={index}
              className="w-full"
            />
          ))}
        </div>
      )}

      {/* Timeline Scrollbar */}
      {monthMarkers.length > 0 && (
        <TimelineScrollbar
          scrollableRef={scrollableRef}
          monthMarkers={monthMarkers}
          className="absolute top-0 right-0 h-full w-4"
        />
      )}

      {/* Media viewer modal */}
      {isImageViewOpen && (
        <MediaView images={displayImages} onClose={handleCloseMediaView} />
      )}
    </div>
  );
};
