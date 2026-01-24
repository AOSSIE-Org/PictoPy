import { useEffect, useRef, useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { FaceCollections } from '@/components/FaceCollections';
import { Image } from '@/types/Media';
import {
  setImages,
  appendImages,
  setPagination,
  setLoadingMore,
} from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import {
  selectImages,
  selectHasNextPage,
  selectIsLoadingMore,
  selectPagination,
} from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchPaginatedImages } from '@/api/api-functions';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { EmptyAITaggingState } from '@/components/EmptyStates/EmptyAITaggingState';
import { PaginatedAPIResponse } from '@/types/API';

const IMAGES_PER_PAGE = 50;

export const AITagging = () => {
  const dispatch = useDispatch();
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const taggedImages = useSelector(selectImages);
  const pagination = useSelector(selectPagination);
  const hasNextPage = useSelector(selectHasNextPage);
  const isLoadingMore = useSelector(selectIsLoadingMore);

  const {
    data: imagesData,
    isLoading: imagesLoading,
    isSuccess: imagesSuccess,
    isError: imagesError,
  } = usePictoQuery({
    queryKey: ['images', 'paginated', 'tagged', 1],
    queryFn: () => fetchPaginatedImages(1, IMAGES_PER_PAGE, true),
  });

  useEffect(() => {
    if (imagesLoading) {
      dispatch(showLoader('Loading AI tagging data'));
    } else if (imagesError) {
      dispatch(hideLoader());
    } else if (imagesSuccess && imagesData) {
      const paginatedData = imagesData as PaginatedAPIResponse<Image>;
      dispatch(setImages(paginatedData.data));
      if (paginatedData.pagination) {
        dispatch(setPagination(paginatedData.pagination));
      }
      dispatch(hideLoader());
    }
  }, [imagesData, imagesSuccess, imagesError, imagesLoading, dispatch]);

  // Load more images function for infinite scroll
  const loadMoreImages = useCallback(async () => {
    if (isLoadingMore || !hasNextPage) return;

    const nextPage = pagination.page + 1;
    dispatch(setLoadingMore(true));

    try {
      const response = await fetchPaginatedImages(
        nextPage,
        IMAGES_PER_PAGE,
        true,
      );
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
  }, [dispatch, hasNextPage, isLoadingMore, pagination.page]);

  return (
    <div className="relative flex h-full flex-col pr-6">
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        <h1 className="mt-6 mb-6 text-2xl font-bold">AI Tagging</h1>

        {/* Face Collections Section */}
        <div className="mb-8">
          <FaceCollections />
        </div>

        {/* Gallery Section */}
        <div className="flex-1">
          {taggedImages.length > 0 ? (
            <ChronologicalGallery
              images={taggedImages}
              showTitle={true}
              title="All Images"
              onMonthOffsetsChange={setMonthMarkers}
              scrollContainerRef={scrollableRef}
              onLoadMore={loadMoreImages}
              hasMore={hasNextPage}
              isLoadingMore={isLoadingMore}
            />
          ) : (
            !imagesLoading && <EmptyAITaggingState />
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
