import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { selectImages } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

// NEW IMPORTS FOR TEXT SEARCH
import { useImageSearch } from '@/hooks/useImageSearch';

export const Home = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);

  // SEARCH STATE
  const searchState = useSelector((state: RootState) => state.search);
  const isTextSearchActive = searchState.active && searchState.type === 'text';
  const searchQuery = searchState.query || '';
  const isFaceSearchActive = searchState.active && searchState.type === 'face';

  // FETCH NORMAL IMAGES WHEN NO SEARCH
  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
    enabled: !searchState.active, // disable when ANY search is active
  });

  // TEXT SEARCH HOOK
  const {
    data: searchData,
    isLoading: searchLoading,
    isSuccess: searchSuccess,
  } = useImageSearch(searchQuery, isTextSearchActive);

  // LOADING STATUS
  const finalLoading = isTextSearchActive ? searchLoading : isLoading;

  // FEEDBACK HANDLER
  useMutationFeedback(
    {
      isPending: finalLoading,
      isSuccess: isTextSearchActive ? searchSuccess : isSuccess,
      isError,
      error,
    },

    {
      loadingMessage: 'Loading images',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load images. Please try again later.',
    },
  );

  // UPDATE IMAGES ON TEXT SEARCH OR NORMAL FETCH
  useEffect(() => {
    if (isTextSearchActive && searchSuccess) {
      const images = searchData?.data as Image[];
      dispatch(setImages(images));
    } else if (!searchState.active && isSuccess) {
      const images = data?.data as Image[];
      dispatch(setImages(images));
    }
  }, [
    dispatch,
    isTextSearchActive,
    searchSuccess,
    searchData,
    searchState.active,
    data,
    isSuccess,
  ]);

  // TITLE
  const title = isTextSearchActive
    ? `Search Results for "${searchQuery}" (${images.length} found)`
    : isFaceSearchActive && images.length > 0
      ? `Face Search Results (${images.length} found)`
      : 'Image Gallery';

  return (
    <div className="relative flex h-full flex-col pr-6">
      {/* Gallery Section */}
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        {images.length > 0 ? (
          <ChronologicalGallery
            images={images}
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
    </div>
  );
};
