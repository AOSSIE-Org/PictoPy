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
import { useNavigate, useParams } from 'react-router';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { ROUTES } from '@/constants/routes';
export const SearchImages = () => {
  const dispatch = useDispatch();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);

  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;
  const searchResults = searchState.images;
  const query = useParams().query || '';

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
    enabled: !isSearchActive,
  });

  // Handle fetching lifecycle
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

  // Filter by month
  const filterImagesByMonthYear = (
    images: Image[],
    monthYearString: string | null,
  ) => {
    if (!monthYearString) return images;

    return images.filter((img) => {
      console.log(img);
      const dateCreated = new Date(img.metadata.date_created);
      const imgMonthYear = dateCreated.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      });
      return imgMonthYear === monthYearString;
    });
  };

  // Format query
  const selectedMonthYear = query
    ? query
        .split(' ')
        .map(
          (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
        )
        .join(' ')
    : null;
  const navigate = useNavigate();
  const baseImages = isSearchActive ? searchResults : images;
  const displayImages = filterImagesByMonthYear(baseImages, selectedMonthYear);

  const title = selectedMonthYear
    ? `${selectedMonthYear} (${displayImages.length} images)`
    : isSearchActive && searchResults.length > 0
      ? `Face Search Results (${searchResults.length} found)`
      : 'All Images';

  return (
    <div className="p-6">
      <Button
        variant="outline"
        onClick={() => {
          console.log("sfvpoisfvipnfi")
          navigate(`/${ROUTES.HOME}`);
        }}
        className="flex items-center gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Home
      </Button>
      <br />
      <h1 className="mb-6 text-2xl font-bold">{title}</h1>

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

      {/* Media viewer modal */}
      {isImageViewOpen && <MediaView images={displayImages} />}
    </div>
  );
};
