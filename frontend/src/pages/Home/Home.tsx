import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ChronologicalGallery } from '@/components/Media/ChronologicalGallery';
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
    <div className="flex h-full flex-col p-6">
      {/* Gallery Section */}
      <div className="flex-1">
        <ChronologicalGallery
          images={images}
          showTitle={true}
          title="Image Gallery"
        />
      </div>

      {/* Media viewer modal */}
      {isImageViewOpen && <MediaView onClose={handleCloseMediaView} />}
    </div>
  );
};
