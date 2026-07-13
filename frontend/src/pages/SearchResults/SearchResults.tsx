import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { Image, ScoredImage } from '@/types/Media';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import {
  searchImagesByTag,
  semanticSearchImages,
  fetchModelStatus,
} from '@/api/api-functions';
import { getErrorMessage } from '@/lib/utils';
import { isSemanticSearchAvailable } from '@/types/models';
import { useNavigate, useSearchParams } from 'react-router';
import { ROUTES } from '@/constants/routes';
import { Button } from '@/components/ui/button';
import { ArrowLeft, AlertCircle } from 'lucide-react';

export const SearchResults = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('value') || '';
  const mode = searchParams.get('mode') || 'auto';
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const displayImages = useSelector(selectImages);

  const [searchError, setSearchError] = useState<string | null>(null);

  const { data: statusData, isSuccess: isStatusSuccess } = usePictoQuery({
    queryKey: ['models', 'status'],
    queryFn: fetchModelStatus,
  });

  const semanticAvailable =
    isStatusSuccess && statusData?.data
      ? isSemanticSearchAvailable(statusData.data)
      : false;

  const { data, isLoading, isSuccess, isError, errorMessage, error } =
    usePictoQuery({
      queryKey: ['search-results', query, mode],
      queryFn: async () => {
        if (mode === 'semantic') {
          const res = await semanticSearchImages({ query });
          (res as any)._resultType = 'semantic';
          return res;
        }
        if (mode === 'tag') {
          const res = await searchImagesByTag({ tag: query });
          (res as any)._resultType = 'tag';
          return res;
        }

        // auto mode
        const tagResponse = await searchImagesByTag({ tag: query });
        if (tagResponse.data && tagResponse.data.length > 0) {
          (tagResponse as any)._resultType = 'tag';
          return tagResponse;
        }

        const statusRes = await fetchModelStatus();
        const semAvailable =
          statusRes.success && statusRes.data
            ? isSemanticSearchAvailable(statusRes.data)
            : false;

        if (semAvailable) {
          dispatch(showLoader('Searching by meaning...'));
          const semResponse = await semanticSearchImages({ query });
          (semResponse as any)._resultType = 'semantic';
          return semResponse;
        }

        (tagResponse as any)._resultType = 'tag';
        return tagResponse;
      },
      enabled: !!query,
    });

  const effectiveMode = (data as any)?._resultType || mode;

  useEffect(() => {
    if (isLoading) {
      setSearchError(null);
      dispatch(showLoader('Searching images'));
    } else if (isError) {
      const errorMsg = getErrorMessage(error, errorMessage);
      if (
        (mode === 'semantic' || mode === 'auto') &&
        errorMsg.includes('Not Found')
      ) {
        dispatch(
          showInfoDialog({
            title: 'Semantic Search Unavailable',
            message: errorMsg,
            variant: 'error',
          }),
        );
      }
      setSearchError(errorMsg || 'Failed to search images');
      dispatch(hideLoader());
    } else if (isSuccess && data) {
      setSearchError(null);
      let fetchedImages: Image[] = [];
      const resultType = (data as any)._resultType || mode;

      if (resultType === 'semantic') {
        fetchedImages = (data?.data?.images ?? []) as ScoredImage[];
      } else {
        fetchedImages = (data?.data ?? []) as Image[];
      }
      dispatch(setImages(fetchedImages));
      dispatch(hideLoader());
    }

    return () => {
      dispatch(hideLoader());
    };
  }, [
    data,
    isSuccess,
    isError,
    isLoading,
    errorMessage,
    error,
    mode,
    dispatch,
  ]);

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

      {isSuccess &&
        displayImages.length > 0 &&
        effectiveMode === 'tag' &&
        semanticAvailable && (
          <div className="mb-4">
            <Button
              variant="outline"
              size="sm"
              className="hover:bg-accent cursor-pointer rounded-full text-xs"
              onClick={() =>
                navigate(
                  `/${ROUTES.SEARCH}?value=${encodeURIComponent(query)}&mode=semantic`,
                )
              }
            >
              Search by meaning instead
            </Button>
          </div>
        )}

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
          {effectiveMode === 'semantic' ? (
            <p>No matches found. Try describing the photo differently.</p>
          ) : (
            <p>No images found matching your search.</p>
          )}
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
