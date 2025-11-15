import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useInfiniteQuery } from '@tanstack/react-query';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { selectImages } from '@/features/imageSelectors';
import { fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import {
  IMAGES_PER_PAGE,
  SCROLL_THRESHOLD,
  DEFAULT_RETRY_COUNT,
  DEFAULT_RETRY_DELAY,
  DEFAULT_STALE_TIME,
} from '@/config/pagination';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export const Home = () => {
  const dispatch = useDispatch();
  const reduxImages = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;

  const {
    data,
    isLoading,
    isSuccess,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['images'],
    queryFn: ({ pageParam = 0 }) =>
      fetchAllImages({ limit: IMAGES_PER_PAGE, offset: pageParam }),
    getNextPageParam: (lastPage) => {
      const total = lastPage?.total ?? 0;
      const currentOffset = lastPage?.offset ?? 0;
      const limit = lastPage?.limit ?? IMAGES_PER_PAGE;
      const nextOffset = currentOffset + limit;
      
      return nextOffset < total ? nextOffset : undefined;
    },
    initialPageParam: 0,
    enabled: !isSearchActive,
    staleTime: DEFAULT_STALE_TIME,
    placeholderData: (previousData) => previousData,
    retry: DEFAULT_RETRY_COUNT,
    retryDelay: DEFAULT_RETRY_DELAY,
  });

  const handleScroll = useCallback(() => {
    if (!scrollableRef.current || !hasNextPage || isFetchingNextPage) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollableRef.current;
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;

    if (scrollPercentage > SCROLL_THRESHOLD) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  useEffect(() => {
    const scrollElement = scrollableRef.current;
    if (!scrollElement) return;

    scrollElement.addEventListener('scroll', handleScroll);
    return () => scrollElement.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  const allImages = useMemo(() => {
    if (!data?.pages) return [];
    return data.pages.flatMap((page) => (page?.data as Image[]) || []);
  }, [data?.pages]);

  useEffect(() => {
    if (!isSearchActive && isSuccess) {
      dispatch(setImages(allImages));
    }
  }, [allImages, isSuccess, isSearchActive, dispatch]);

  const images = useMemo(() => {
    return isSearchActive ? reduxImages : allImages;
  }, [isSearchActive, reduxImages, allImages]);

  useMutationFeedback(
    { isPending: isLoading && !isSearchActive, isSuccess, isError, error },
    {
      loadingMessage: 'Loading images',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load images. Please try again later.',
    },
  );

  const title = useMemo(() => {
    return isSearchActive && images.length > 0
      ? `Face Search Results (${images.length} found)`
      : 'Image Gallery';
  }, [isSearchActive, images.length]);

  return (
    <div className="relative flex h-full flex-col pr-6">
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        {images.length > 0 ? (
          <>
            <ChronologicalGallery
              images={images}
              showTitle={true}
              title={title}
              onMonthOffsetsChange={setMonthMarkers}
              scrollContainerRef={scrollableRef}
            />
            {isFetchingNextPage && (
              <div className="py-4 text-center text-sm text-gray-500">
                Loading more images...
              </div>
            )}
          </>
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
