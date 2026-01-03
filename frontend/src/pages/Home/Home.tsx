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

import { MediaInfoPanel } from '@/components/Media/MediaInfoPanel';

export const Home = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;

  // Media Info Modal State
  const [isInfoOpen, setIsInfoOpen] = useState(false);
  const [infoImage, setInfoImage] = useState<Image | null>(null);
  const [infoIndex, setInfoIndex] = useState<number>(0);

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
      const images = data?.data as Image[];
      dispatch(setImages(images));
    }
  }, [data, isSuccess, dispatch, isSearchActive]);

  const title =
    isSearchActive && images.length > 0
      ? `Face Search Results (${images.length} found)`
      : 'Image Gallery';

  const handleOpenInfo = (image: Image, index: number) => {
    setInfoImage(image);
    setInfoIndex(index);
    setIsInfoOpen(true);
  };

  const handleCloseInfo = () => {
    setIsInfoOpen(false);
    setInfoImage(null);
  };

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
            onViewInfo={handleOpenInfo}
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

      {/* Media Info Modal Overlay */}
      {isInfoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={handleCloseInfo}>
          <div onClick={(e) => e.stopPropagation()} className="relative">
            <MediaInfoPanel
              show={isInfoOpen}
              onClose={handleCloseInfo}
              currentImage={infoImage}
              currentIndex={infoIndex}
              totalImages={images.length}
              className="static top-0 left-0 w-[400px] m-0! border-white/20 shadow-2xl"
            />
          </div>
        </div>
      )}
    </div>
  );
};
