// src/pages/Home/Home.tsx
import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';

import { ViewModeToggle } from '@/components/ViewModeToggle';
import { GalleryView } from '@/components/GalleryView';

export const Home = () => {
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

  const title =
    isSearchActive && images.length > 0
      ? `Face Search Results (${images.length} found)`
      : 'Image Gallery';

  return (
    <div className="relative flex h-full flex-col pr-6">
      <ViewModeToggle />

      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        {images.length > 0 ? (
          <GalleryView
            images={images as any}
            title={title}
            scrollableRef={scrollableRef}
            onMonthOffsetsChange={setMonthMarkers}
          />
        ) : (
          <EmptyGalleryState />
        )}
      </div>

      {monthMarkers.length > 0 && (
        <TimelineScrollbar
          scrollableRef={scrollableRef}
          monthMarkers={monthMarkers}
          className="absolute top-0 right-0 h-full w-4"
        />
      )}
    </div>
  );
};

export default Home;
