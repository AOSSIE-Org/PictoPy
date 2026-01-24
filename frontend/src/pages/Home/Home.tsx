import { useEffect, useRef, useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import {
  setImages,
  appendImages,
  setPagination,
  setLoadingMore,
  clearImages,
} from '@/features/imageSlice';
import {
  selectImages,
  selectHasNextPage,
  selectIsLoadingMore,
  selectPagination,
} from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchPaginatedImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { PaginatedAPIResponse } from '@/types/API';

const IMAGES_PER_PAGE = 50;

export const Home = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const pagination = useSelector(selectPagination);
  const hasNextPage = useSelector(selectHasNextPage);
  const isLoadingMore = useSelector(selectIsLoadingMore);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;

  // Initial page load
  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['images', 'paginated', 1],
    queryFn: () => fetchPaginatedImages(1, IMAGES_PER_PAGE),
    enabled: !isSearchActive,
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading images',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load images. Please try again later.',
    },
  );

  // Handle initial data load
  useEffect(() => {
    if (!isSearchActive && isSuccess && data) {
      const paginatedData = data as PaginatedAPIResponse<Image>;
      dispatch(setImages(paginatedData.data));
      if (paginatedData.pagination) {
        dispatch(setPagination(paginatedData.pagination));
      }
    }
  }, [data, isSuccess, dispatch, isSearchActive]);

  // Clear images when search becomes active
  useEffect(() => {
    if (isSearchActive) {
      // Don't clear images during search - let search handle it
    }
  }, [isSearchActive]);

  // Load more images function for infinite scroll
  const loadMoreImages = useCallback(async () => {
    if (isLoadingMore || !hasNextPage || isSearchActive) return;

    const nextPage = pagination.page + 1;
    dispatch(setLoadingMore(true));

    try {
      const response = await fetchPaginatedImages(nextPage, IMAGES_PER_PAGE);
      const paginatedData = response as PaginatedAPIResponse<Image>;

      dispatch(appendImages(paginatedData.data));
      if (paginatedData.pagination) {
        dispatch(setPagination(paginatedData.pagination));
      }
    } catch (err) {
      console.error('Error loading more images:', err);
    } finally {
      dispatch(setLoadingMore(false));
    }
  }, [dispatch, hasNextPage, isLoadingMore, isSearchActive, pagination.page]);

  const title =
    isSearchActive && images.length > 0
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
            onLoadMore={loadMoreImages}
            hasMore={hasNextPage}
            isLoadingMore={isLoadingMore}
          />
        ) : (
          !isLoading && <EmptyGalleryState />
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
