import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { setCurrentViewIndex as setCurrentVideoViewIndex } from '@/features/videoSlice';
import { selectImages } from '@/features/imageSelectors';
import { selectIsVideoViewOpen, selectVideos } from '@/features/videoSelectors';
import { VideoCard } from '@/components/Media/VideoCard';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export const Home = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;
  // Face search can match videos too. Only while searching: otherwise the
  // slice still holds whatever the videos page last loaded.
  const allVideos = useSelector(selectVideos);
  const isVideoViewOpen = useSelector(selectIsVideoViewOpen);
  const matchedVideos = isSearchActive ? allVideos : [];

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
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

  useEffect(() => {
    if (!isSearchActive && isSuccess) {
      const images = (data?.data ?? []) as Image[];
      dispatch(setImages(images));
    }
  }, [data, isSuccess, dispatch, isSearchActive]);

  const title =
    isSearchActive && images.length > 0
      ? `Face Search Results (${images.length + matchedVideos.length} found)`
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
          matchedVideos.length === 0 && <EmptyGalleryState />
        )}

        {/* Videos the searched face was found in */}
        {matchedVideos.length > 0 && (
          <>
            <h2 className="mb-4 text-xl font-semibold">Videos</h2>
            <div className="grid grid-cols-1 gap-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {matchedVideos.map((video, index) => (
                <div key={video.id} className="group relative">
                  <VideoCard
                    video={video}
                    className="w-full transition-transform duration-200 group-hover:scale-105"
                    onClick={() => dispatch(setCurrentVideoViewIndex(index))}
                  />
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {isVideoViewOpen && matchedVideos.length > 0 && (
        <VideoPlayerOverlay videos={matchedVideos} />
      )}

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
