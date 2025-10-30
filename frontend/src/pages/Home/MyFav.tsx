import { useEffect, useMemo, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages} from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import { Heart } from 'lucide-react';

export const MyFav = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
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

  // const handleCloseMediaView = () => {
  //   // MediaView will handle closing via Redux
  // };

  const favouriteImages = useMemo(
    () => images.filter((image) => image.isFavourite === true),
    [images],
  );

  const title =
    isSearchActive && images.length > 0
      ? `Face Search Results (${images.length} found)`
      : 'Favourite Image Gallery';

  if (favouriteImages.length === 0) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold">{title}</h1>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          {/* Heart Icon/Sticker */}
          <div className="bg-muted/50 mb-6 flex h-32 w-32 items-center justify-center rounded-full">
            <Heart />
          </div>

          {/* Text Content */}
          <h2 className="text-foreground mb-3 text-xl font-semibold">
            No Favourite Images Yet
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Start building your collection by marking images as favourites.
            Click the heart icon on any image to add it here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-full flex-col pr-6">
      {/* Gallery Section */}
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        {favouriteImages.length > 0 ? (
          <ChronologicalGallery
            images={favouriteImages}
            showTitle={true}
            title={title}
            onMonthOffsetsChange={setMonthMarkers}
            scrollContainerRef={scrollableRef}
          />
        ) : (
          <EmptyGalleryState />
        )}
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
    </div>
  );
};
