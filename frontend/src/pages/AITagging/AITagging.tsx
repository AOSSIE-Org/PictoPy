import { useEffect, useRef, useState,useMemo } from 'react';
import { RootState } from '@/app/store';
import { useDispatch, useSelector } from 'react-redux';
import { FaceCollections } from '@/components/FaceCollections';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { EmptyAITaggingState } from '@/components/EmptyStates/EmptyAITaggingState';

export const AITagging = () => {
  const dispatch = useDispatch();
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const taggedImages = useSelector(selectImages);
  const tagQuery = useSelector(
    (state: RootState) => state.search.tagQuery
  );
  const filteredImages = useMemo(() => {
    if (!tagQuery.trim()) return taggedImages;

    const q = tagQuery.toLowerCase();
    
    return taggedImages.filter((img) =>
      img.tags?.some((tag) => tag.toLowerCase().includes(q))
  );
}, [taggedImages, tagQuery]);
  const {
    data: imagesData,
    isLoading: imagesLoading,
    isSuccess: imagesSuccess,
    isError: imagesError,
  } = usePictoQuery({
    queryKey: ['images', { tagged: true }],
    queryFn: () => fetchAllImages(true),
  });

  useEffect(() => {
    if (imagesLoading) {
      dispatch(showLoader('Loading AI tagging data'));
    } else if (imagesError) {
      dispatch(hideLoader());
    } else if (imagesSuccess) {
      const images = imagesData?.data as Image[];
      dispatch(setImages(images));
      dispatch(hideLoader());
    }
  }, [imagesData, imagesSuccess, imagesError, imagesLoading, dispatch]);

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
          {taggedImages.length === 0 ? (
            <EmptyAITaggingState />
          ) : filteredImages.length === 0 ? (
          <div className="flex h-40 items-center justify-center text-muted-foreground">
            No images match "{tagQuery}"
            </div>
            ) : (
            <ChronologicalGallery
            images={filteredImages}
            showTitle={true}
            title={
              tagQuery
              ? `Tag Search Results (${filteredImages.length} found)`
              : 'All Images'
            }
            onMonthOffsetsChange={setMonthMarkers}
            scrollContainerRef={scrollableRef}
            />
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
