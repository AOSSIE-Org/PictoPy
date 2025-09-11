import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
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

  const searchState = useSelector((state: any) => state.search);
  const isSearchActive = searchState.active;
  const searchResults = searchState.images;
  const isSearchLoading = searchState.loading;

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
    enabled: !isSearchActive,
  });

  useEffect(() => {
    // Handle regular image loading
    if (!isSearchActive) {
      if (isLoading) {
        dispatch(showLoader('Loading images'));
      } else if (isError) {
        dispatch(hideLoader());
      } else if (isSuccess) {
        const images = data?.data as Image[];
        dispatch(setImages(images));
        dispatch(hideLoader());
      }
    }
  }, [data, isSuccess, isError, isLoading, dispatch, isSearchActive]);

  useEffect(() => {
    if (isSearchActive) {
      if (isSearchLoading) {
        dispatch(showLoader('Searching for similar faces...'));
      } else {
        dispatch(hideLoader());
      }
    }
  }, [isSearchActive, isSearchLoading, dispatch]);

  const handleCloseMediaView = () => {
    // MediaView will handle closing via Redux
  };
  const displayImages = isSearchActive ? searchResults : images;
  const title = isSearchActive
    ? `Face Search Results (${searchResults.length} found)`
    : 'Image Gallery';
  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold">{title}</h1>

      {/* Show message when search is active but no results */}
      {isSearchActive && searchResults.length === 0 && !isSearchLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-muted-foreground mb-2 text-lg">
              No matching faces found
            </p>
            <p className="text-muted-foreground text-sm">
              Try uploading a different image or clear the search to see all
              images
            </p>
          </div>
        </div>
      )}

      {/* Image Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {displayImages.map((image, index) => (
          <ImageCard
            key={image.id}
            image={image}
            imageIndex={index}
            className="w-full"
          />
        ))}
      </div>

      {/* Media Viewer Modal */}
      {isImageViewOpen && <MediaView onClose={handleCloseMediaView} />}
    </div>
  );
};
