import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useDispatch } from 'react-redux';
import { useInfiniteQuery } from '@tanstack/react-query';
import { FaceCollections } from '@/components/FaceCollections';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { fetchAllImages } from '@/api/api-functions';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { EmptyAITaggingState } from '@/components/EmptyStates/EmptyAITaggingState';
import {
  IMAGES_PER_PAGE,
  SCROLL_THRESHOLD,
  DEFAULT_RETRY_COUNT,
  DEFAULT_RETRY_DELAY,
  DEFAULT_STALE_TIME,
} from '@/config/pagination';

export const AITagging = () => {
  const dispatch = useDispatch();
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);

  const {
    data,
    isLoading,
    isSuccess,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isFetching,
    isRefetching,
  } = useInfiniteQuery({
    queryKey: ['images', { tagged: true }],
    queryFn: ({ pageParam = 0 }) =>
      fetchAllImages({ tagged: true, limit: IMAGES_PER_PAGE, offset: pageParam }),
    getNextPageParam: (lastPage) => {
      const total = lastPage?.total ?? 0;
      const currentOffset = lastPage?.offset ?? 0;
      const limit = lastPage?.limit ?? IMAGES_PER_PAGE;
      const nextOffset = currentOffset + limit;
      
      return nextOffset < total ? nextOffset : undefined;
    },
    initialPageParam: 0,
    staleTime: DEFAULT_STALE_TIME,
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
    if (isSuccess) {
      dispatch(setImages(allImages));
    }
  }, [allImages, isSuccess, dispatch]);

  const displayImages = allImages;

  useEffect(() => {
    const shouldShowLoader = isLoading || (isRefetching && !isFetchingNextPage);
    
    if (shouldShowLoader) {
      dispatch(showLoader('Loading AI tagging data'));
    } else {
      dispatch(hideLoader());
    }
  }, [isLoading, isFetching, isFetchingNextPage, isRefetching, dispatch]);

  return (
    <div className="relative flex h-full flex-col pr-6">
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        <h1 className="mt-6 mb-6 text-2xl font-bold">AI Tagging</h1>

        <div className="mb-8">
          <FaceCollections />
        </div>

        <div className="flex-1">
          {displayImages.length > 0 ? (
            <>
              <ChronologicalGallery
                images={displayImages}
                showTitle={true}
                title="All Images"
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
            <EmptyAITaggingState />
          )}
        </div>
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
