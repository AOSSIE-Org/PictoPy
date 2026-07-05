import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { Image } from '@/types/Media';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { searchImagesByTag } from '@/api/api-functions';
import { useNavigate, useSearchParams } from 'react-router';
import { Button } from '@/components/ui/button';
import { ArrowLeft, AlertCircle } from 'lucide-react';

export const SearchResults = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('value') || '';
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const displayImages = useSelector(selectImages);

  const [searchError, setSearchError] = useState<string | null>(null);

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['search-results', query],
    queryFn: async () => searchImagesByTag({ tag: query }),
    enabled: !!query,
  });

  useEffect(() => {
    if (isLoading) {
      setSearchError(null);
      dispatch(showLoader('Searching images'));
    } else if (isError) {
      setSearchError(error?.message || 'Failed to search images');
      dispatch(hideLoader());
    } else if (isSuccess) {
      setSearchError(null);
      const fetchedImages = (data?.data ?? []) as Image[];
      dispatch(setImages(fetchedImages));
      dispatch(hideLoader());
    }

    return () => {
      dispatch(hideLoader());
    };
  }, [data, isSuccess, isError, isLoading, dispatch]);

  return (
    <div>
      <div className="my-6 flex items-center justify-between">
        <Button
          variant="outline"
          onClick={() => navigate(-1)}
          className="flex cursor-pointer items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>
      <h1 className="mb-6 text-2xl font-bold">Results for "{query}"</h1>
      {searchError ? (
        <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
          <AlertCircle className="text-destructive mb-4 h-12 w-12" />
          <h3 className="text-destructive mb-2 text-xl font-medium">
            Search Failed
          </h3>
          <p>{searchError}</p>
        </div>
      ) : !query ? (
        <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
          <p>Please enter a search term to find images.</p>
        </div>
      ) : displayImages.length === 0 && isSuccess ? (
        <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
          <p>No images found matching your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {displayImages.map((image, index) => (
            <div key={image.id} className="group relative">
              <ImageCard
                image={image}
                imageIndex={index}
                className="w-full transition-transform duration-200 group-hover:scale-105"
                onClick={() => dispatch(setCurrentViewIndex(index))}
              />
            </div>
          ))}
        </div>
      )}

      {/* Media Viewer Modal */}
      {isImageViewOpen && <MediaView images={displayImages} />}
    </div>
  );
};
