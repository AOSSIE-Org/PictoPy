import { useEffect, useMemo, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalFavoritesGallery,
  type FavoritesSortValue,
} from '@/components/Media/ChronologicalFavoritesGallery';
import { MonthMarker } from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { setImages } from '@/features/imageSlice';
import { selectImages } from '@/features/imageSelectors';
import { setVideos } from '@/features/videoSlice';
import { selectVideos } from '@/features/videoSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { usePersistedSort } from '@/hooks/usePersistedSort';
import { fetchAllImages, fetchAllVideos } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import { Calendar, Heart, ListOrdered } from 'lucide-react';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import {
  GallerySortDropdown,
  type SortOption,
} from '@/components/GallerySortDropdown';

const FAV_SORT_OPTIONS: SortOption<FavoritesSortValue>[] = [
  { value: 'date', label: 'Date', icon: Calendar },
  { value: 'custom', label: 'Custom', icon: ListOrdered },
];

const FAV_SORT_STORAGE_KEY = 'pictopy-favorites-sort';
const FAV_SORT_VALUES = FAV_SORT_OPTIONS.map((option) => option.value);

export const MyFav = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const videos = useSelector(selectVideos);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;
  const [sortBy, setSortBy] = usePersistedSort<FavoritesSortValue>(
    FAV_SORT_STORAGE_KEY,
    'date',
    FAV_SORT_VALUES,
  );

  const {
    data: imageData,
    isLoading: isImagesLoading,
    isSuccess: isImagesSuccess,
    isError: isImagesError,
    error: imagesError,
  } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
    enabled: !isSearchActive,
  });

  const {
    data: videoData,
    isLoading: isVideosLoading,
    isSuccess: isVideosSuccess,
    isError: isVideosError,
    error: videosError,
  } = usePictoQuery({
    queryKey: ['videos'],
    queryFn: () => fetchAllVideos(),
    enabled: !isSearchActive,
  });

  // A single feedback call owns the global loader, kept up for as long as
  // either query is pending -- two independent calls would each hide it the
  // moment their own query settles, blanking it while the other still loads.
  useMutationFeedback(
    { isPending: isImagesLoading || isVideosLoading },
    {
      loadingMessage: 'Loading favorites',
      showSuccess: false,
      showError: false,
    },
  );

  useMutationFeedback(
    {
      isSuccess: isImagesSuccess,
      isError: isImagesError,
      error: imagesError,
    },
    {
      showLoading: false,
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load images. Please try again later.',
    },
  );

  useMutationFeedback(
    {
      isSuccess: isVideosSuccess,
      isError: isVideosError,
      error: videosError,
    },
    {
      showLoading: false,
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load videos. Please try again later.',
    },
  );

  // Handle fetching lifecycle
  useEffect(() => {
    if (!isSearchActive && isImagesSuccess) {
      dispatch(setImages(imageData?.data ?? []));
    }
  }, [imageData, isImagesSuccess, dispatch, isSearchActive]);

  useEffect(() => {
    if (!isSearchActive && isVideosSuccess) {
      dispatch(setVideos(videoData?.data ?? []));
    }
  }, [videoData, isVideosSuccess, dispatch, isSearchActive]);

  const favouriteImages = useMemo(
    () => images.filter((image) => image.isFavourite === true),
    [images],
  );

  const favouriteVideos = useMemo(
    // The video query is disabled during search, but the store still holds
    // whatever favourited videos were loaded before search started -- don't
    // let them leak into the face-search results.
    () =>
      isSearchActive
        ? []
        : videos.filter((video) => video.isFavourite === true),
    [videos, isSearchActive],
  );

  const favouriteCount = favouriteImages.length + favouriteVideos.length;

  const title =
    isSearchActive && images.length > 0
      ? `Face Search Results (${images.length} found)`
      : 'Favorites';

  if (favouriteCount === 0) {
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
            No Favorites Yet
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Start building your collection by marking images and videos as
            favorites. Click the heart icon on any item to add it here.
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
        {favouriteCount > 0 ? (
          <ChronologicalFavoritesGallery
            images={favouriteImages}
            videos={favouriteVideos}
            sortBy={sortBy}
            showTitle={true}
            title={title}
            titleRight={
              !isSearchActive && (
                <GallerySortDropdown
                  value={sortBy}
                  onValueChange={setSortBy}
                  options={FAV_SORT_OPTIONS}
                />
              )
            }
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
