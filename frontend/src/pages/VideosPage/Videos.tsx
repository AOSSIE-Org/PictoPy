import { useEffect, useRef, useState } from 'react';
import { Film } from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';
import { ChronologicalVideoGallery } from '@/components/Media/ChronologicalVideoGallery';
import { MonthMarker } from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Video } from '@/types/Media';
import { setVideos } from '@/features/videoSlice';
import { selectVideos } from '@/features/videoSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllVideos } from '@/api/api-functions';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export const Videos = () => {
  const dispatch = useDispatch();
  const videos = useSelector(selectVideos);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['videos'],
    queryFn: () => fetchAllVideos(),
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading videos',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load videos. Please try again later.',
    },
  );

  useEffect(() => {
    if (isSuccess) {
      const videos = (data?.data ?? []) as Video[];
      dispatch(setVideos(videos));
    }
  }, [data, isSuccess, dispatch]);

  return (
    <div className="relative flex h-full flex-col pr-6">
      {/* Gallery Section */}
      <div
        ref={scrollableRef}
        className="hide-scrollbar min-h-0 flex-1 overflow-x-hidden overflow-y-auto"
      >
        {videos.length > 0 ? (
          <ChronologicalVideoGallery
            videos={videos}
            showTitle={true}
            title="Video Gallery"
            onMonthOffsetsChange={setMonthMarkers}
            scrollContainerRef={scrollableRef}
          />
        ) : (
          <EmptyGalleryState
            title="No Videos to Display"
            description="Your gallery is empty. Please add a folder containing videos to get started."
            formatsHint="Supports MP4, MOV, WebM, M4V video formats."
            formatsIcon={Film}
          />
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
