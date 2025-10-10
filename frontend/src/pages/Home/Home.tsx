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
    console.log(images);
  }, [data, isSuccess, isError, isLoading, dispatch, isSearchActive]);

  const handleCloseMediaView = () => {
    // MediaView will handle closing via Redux
  };

  const displayImages = isSearchActive ? searchResults : images;
  useEffect(() => {
    console.log('Display Images Updated:', displayImages);
  }, [displayImages]);

  const title =
    isSearchActive && searchResults.length > 0
      ? `Face Search Results (${searchResults.length} found)`
      : 'Image Gallery';

  return (
    <div className="relative flex h-full flex-col pr-6">
      {/* Gallery Section */}
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        <ChronologicalGallery
          images={displayImages}
          showTitle={true}
          title={title}
          onMonthOffsetsChange={setMonthMarkers}
          scrollContainerRef={scrollableRef}
        />
      </div>

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
