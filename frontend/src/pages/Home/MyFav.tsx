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
import { RootState } from '@/app/store';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { Heart } from 'lucide-react';
export const MyFav = () => {
  const dispatch = useDispatch();

  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;
  const searchResults = searchState.images;

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
    enabled: !isSearchActive,
  });

  useEffect(() => {
    if (!isSearchActive) {
      if (isLoading) {
        dispatch(showLoader('Loading images'));
      } else if (isError) {
        dispatch(hideLoader());
        dispatch(
          showInfoDialog({
            title: 'Error',
            message: 'Failed to load images. Please try again later.',
            variant: 'error',
          }),
        );
      } else if (isSuccess) {
        const images = data?.data as Image[];
        dispatch(setImages(images));
        dispatch(hideLoader());
      }
    }
  }, [data, isSuccess, isError, isLoading, dispatch, isSearchActive]);

  const handleCloseMediaView = () => {};

  const displayImages = isSearchActive ? searchResults : images;
  const favouriteImages = displayImages.filter(
    (image) => image.isFavourite === true,
  );
  const title =
    isSearchActive && searchResults.length > 0
      ? `Face Search Results (${searchResults.length} found)`
      : 'Favourite Image Gallery';

  if (favouriteImages.length === 0) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold">{title}</h1>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          {/* Heart Icon/Sticker */}
          <div className="bg-muted/50 mb-6 flex h-32 w-32 items-center justify-center rounded-full">
            <Heart />
          </div>

          {/* Text Content */}
          <h2 className="text-foreground mb-3 text-xl font-semibold">
            No Favourite Images Yet
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Start building your collection by marking images as favourites.
            Click the heart icon on any image to add it here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold">{title}</h1>

      {/* Image Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {favouriteImages.map((image, index) => (
          <ImageCard
            key={image.id}
            image={image}
            imageIndex={index}
            className="w-full"
          />
        ))}
      </div>

      {/* Media Viewer Modal */}
      {isImageViewOpen && (
        <MediaView images={favouriteImages} onClose={handleCloseMediaView} />
      )}
    </div>
  );
};
