import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { MediaView } from '@/components/Media/MediaView';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';

export const Home = () => {
  const dispatch = useDispatch();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
  });

  useEffect(() => {
    if (isLoading) {
      dispatch(showLoader('Loading images'));
    } else if (isError) {
      dispatch(hideLoader());
    } else if (isSuccess) {
      const images = data?.data as Image[];
      dispatch(setImages(images));
      dispatch(hideLoader());
    }
  }, [data, isSuccess, isError, isLoading, dispatch]);

  const handleCloseMediaView = () => {
    // MediaView will handle closing via Redux
  };
  return (
    <div className="relative flex h-full flex-col pr-6">
      {/* Gallery Section */}
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        <ChronologicalGallery
          images={images}
          showTitle={true}
          title="Image Gallery"
          onMonthOffsetsChange={setMonthMarkers}
          scrollContainerRef={scrollableRef}
        />
      </div>

      {/* Timeline Scrollbar */}
      <TimelineScrollbar
        scrollableRef={scrollableRef}
        monthMarkers={monthMarkers}
        className="absolute top-0 right-0 h-full w-4"
      />

      {/* Media viewer modal */}
      {isImageViewOpen && <MediaView onClose={handleCloseMediaView} />}
    </div>
  );
};
