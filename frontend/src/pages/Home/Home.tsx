import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useMutation } from '@tanstack/react-query';
import { scanCelebrities } from '@/api/api-functions';
import { Button } from '@/components/ui/button';
import { Sparkles } from 'lucide-react'; 
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

export const Home = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
    enabled: !isSearchActive,
  });

  const scanMutation = useMutation({
    mutationFn: scanCelebrities,
  });

  useMutationFeedback(
    { 
      isPending: scanMutation.isPending, 
      isSuccess: scanMutation.isSuccess, 
      isError: scanMutation.isError, 
      error: scanMutation.error 
    },
    {
      loadingMessage: 'Scanning for celebrities...',
      successMessage: 'Celebrity scan started in background.',
      errorTitle: 'Scan Failed',
      errorMessage: 'Failed to start celebrity scan.',
    },
  );

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
      const images = data?.data as Image[];
      dispatch(setImages(images));
    }
  }, [data, isSuccess, dispatch, isSearchActive]);

  const title =
    isSearchActive && images.length > 0
      ? `Face Search Results (${images.length} found)`
      : 'Image Gallery';

  return (
    <div className="relative flex h-full flex-col pr-6">
      <div className="flex justify-end pb-2 pt-2">
         <Button 
            variant="outline" 
            size="sm" 
            onClick={() => scanMutation.mutate()}
            disabled={scanMutation.isPending}
            className="gap-2"
         >
            <Sparkles className="h-4 w-4" />
            {scanMutation.isPending ? 'Scanning...' : 'Scan Celebrities'}
         </Button>
      </div>

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
