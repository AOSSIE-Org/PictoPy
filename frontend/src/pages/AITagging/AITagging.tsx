import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { MediaView } from '@/components/Media/MediaView';
import { FaceCollections } from '@/components/FaceCollections';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import {
  selectTaggedImages,
  selectIsImageViewOpen,
} from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import {
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { ImageCard } from '@/components/Media/ImageCard';
import { Bot, Tags, Image as ImageIcon } from 'lucide-react';

export const AITagging = () => {
  const dispatch = useDispatch();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const taggedImages = useSelector(selectTaggedImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);

  const {
    data: imagesData,
    isLoading: imagesLoading,
    isSuccess: imagesSuccess,
    isError: imagesError,
  } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
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

      {/* Image Grid */}
      <div className="mb-6">
        <h2 className="mb-4 text-xl font-semibold">All Images</h2>

        {/* Empty State Placeholder */}
        {taggedImages.length === 0 && !imagesLoading && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
              <Bot className="h-16 w-16 text-gray-400" />
            </div>
            <h2 className="mb-2 text-xl font-semibold text-gray-700 dark:text-gray-300">
              No AI Tagged Images
            </h2>
            <p className="mb-6 max-w-md text-gray-500 dark:text-gray-400">
              Your images haven't been processed by AI yet. Add some images to
              your gallery and they will be automatically tagged with AI-powered
              labels.
            </p>
            <div className="flex flex-col gap-2 text-sm text-gray-400 dark:text-gray-500">
              <div className="flex items-center gap-2">
                <Tags className="h-4 w-4" />
                <span>
                  AI will automatically detect objects, people, and scenes
                </span>
              </div>
              <div className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4" />
                <span>Supports PNG, JPG, JPEG, GIF, BMP image formats</span>
              </div>
            </div>
          </div>
        )}

        {/* Image Grid */}
        {taggedImages.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {taggedImages.map((image, index) => (
              <ImageCard
                key={image.id}
                image={image}
                imageIndex={index}
                className="w-full"
              />
            ))}
          </div>
        )}
      </div>

        {/* Media Viewer Modal */}
        {isImageViewOpen && <MediaView images={taggedImages} />}
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
