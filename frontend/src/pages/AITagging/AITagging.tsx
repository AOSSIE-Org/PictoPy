import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { FaceCollections } from '@/components/FaceCollections';
import { EmptyAITaggingState } from '@/components/EmptyStates/EmptyAITaggingState';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import {
  selectTaggedImages,
  selectIsImageViewOpen,
} from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';

export const AITagging = () => {
  const dispatch = useDispatch();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const taggedImages = useSelector(selectTaggedImages);

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
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold">AI Tagging</h1>

      {/* Face Collections Section */}
      <div className="mb-8">
        <FaceCollections />
      </div>

      {/* Image Grid */}
      <div className="mb-6">
        <h2 className="mb-4 text-xl font-semibold">All Images</h2>

        {/* Empty State Placeholder */}
        {taggedImages.length === 0 && !imagesLoading && <EmptyAITaggingState />}

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
  );
};
