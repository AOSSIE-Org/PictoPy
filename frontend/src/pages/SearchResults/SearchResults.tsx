import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AxiosError } from 'axios';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { VideoCard } from '@/components/Media/VideoCard';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';
import { Image, ScoredImage, ScoredVideo, Video } from '@/types/Media';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import {
  setCurrentViewIndex as setCurrentVideoViewIndex,
  setVideos,
} from '@/features/videoSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { selectIsVideoViewOpen, selectVideos } from '@/features/videoSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import {
  searchImagesByTag,
  semanticSearchImages,
  searchVideosByTag,
  semanticSearchVideos,
  fetchModelStatus,
  SemanticSearchAPIResponse,
  SemanticSearchVideosAPIResponse,
} from '@/api/api-functions';
import { APIResponse } from '@/types/API';
import { getErrorMessage } from '@/lib/utils';
import { isSemanticSearchAvailable } from '@/types/models';
import { useNavigate, useSearchParams } from 'react-router';
import { ROUTES } from '@/constants/routes';
import { Button } from '@/components/ui/button';
import { ArrowLeft, AlertCircle } from 'lucide-react';

interface TagSearchResult extends APIResponse {
  resultType: 'tag';
}

interface SemanticSearchResult extends SemanticSearchAPIResponse {
  resultType: 'semantic';
}

type SearchQueryResult = TagSearchResult | SemanticSearchResult;

interface VideoTagSearchResult extends APIResponse {
  resultType: 'tag';
}

interface VideoSemanticSearchResult extends SemanticSearchVideosAPIResponse {
  resultType: 'semantic';
}

type VideoSearchQueryResult = VideoTagSearchResult | VideoSemanticSearchResult;

const getHttpStatus = (error: unknown): number | undefined => {
  const axiosErr = error as AxiosError;
  return axiosErr?.isAxiosError ? axiosErr.response?.status : undefined;
};

export const SearchResults = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('value') || '';
  const mode = searchParams.get('mode') || 'auto';
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const displayImages = useSelector(selectImages);
  const isVideoViewOpen = useSelector(selectIsVideoViewOpen);
  const displayVideos = useSelector(selectVideos);

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
      queryFn: async (): Promise<SearchQueryResult> => {
        if (mode === 'semantic') {
          const res = await semanticSearchImages({ query });
          return { ...res, resultType: 'semantic' };
        }
        if (mode === 'tag') {
          const res = await searchImagesByTag({ tag: query });
          return { ...res, resultType: 'tag' };
        }

        // auto mode
        const tagResponse = await searchImagesByTag({ tag: query });
        if (tagResponse.data && tagResponse.data.length > 0) {
          return { ...tagResponse, resultType: 'tag' };
        }

        const statusRes = await fetchModelStatus();
        const semAvailable =
          statusRes.success && statusRes.data
            ? isSemanticSearchAvailable(statusRes.data)
            : false;

        if (semAvailable) {
          dispatch(showLoader('Searching by meaning...'));
          const semResponse = await semanticSearchImages({ query });
          return { ...semResponse, resultType: 'semantic' };
        }

        return { ...tagResponse, resultType: 'tag' };
      },
      enabled: !!query,
    });

  // Videos run as their own query: they share the mode logic but a video
  // failure (e.g. no frames embedded yet) must not blank the image results.
  const { data: videoData, isSuccess: isVideoSuccess } = usePictoQuery({
    queryKey: ['search-results-videos', query, mode],
    queryFn: async (): Promise<VideoSearchQueryResult> => {
      if (mode === 'semantic') {
        const res = await semanticSearchVideos({ query });
        return { ...res, resultType: 'semantic' };
      }

      const tagResponse = await searchVideosByTag({ tag: query });
      if (mode === 'tag' || (tagResponse.data?.length ?? 0) > 0) {
        return { ...tagResponse, resultType: 'tag' };
      }

      const statusRes = await fetchModelStatus();
      const semAvailable =
        statusRes.success && statusRes.data
          ? isSemanticSearchAvailable(statusRes.data)
          : false;

      if (semAvailable) {
        const semResponse = await semanticSearchVideos({ query });
        return { ...semResponse, resultType: 'semantic' };
      }

      return { ...tagResponse, resultType: 'tag' };
    },
    enabled: !!query,
  });

  useEffect(() => {
    if (!isVideoSuccess || !videoData) return;

    const fetchedVideos: Video[] =
      videoData.resultType === 'semantic'
        ? ((videoData.data?.videos ?? []) as ScoredVideo[])
        : ((videoData.data ?? []) as Video[]);

    dispatch(setVideos(fetchedVideos));
  }, [videoData, isVideoSuccess, dispatch]);

  const effectiveMode = data?.resultType || mode;

  useEffect(() => {
    if (isLoading) {
      setSearchError(null);
      dispatch(showLoader('Searching images'));
    } else if (isError) {
      const errorMsg = getErrorMessage(error, errorMessage);
      const httpStatus = getHttpStatus(error);
      if ((mode === 'semantic' || mode === 'auto') && httpStatus === 404) {
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

      if (data.resultType === 'semantic') {
        fetchedImages = (data.data?.images ?? []) as ScoredImage[];
      } else {
        fetchedImages = (data.data ?? []) as Image[];
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
      ) : displayImages.length === 0 &&
        displayVideos.length === 0 &&
        isSuccess ? (
        <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
          {effectiveMode === 'semantic' ? (
            <p>No matches found. Try describing it differently.</p>
          ) : (
            <p>No photos or videos found matching your search.</p>
          )}
        </div>
      ) : (
        <>
          {displayImages.length > 0 && (
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

          {displayVideos.length > 0 && (
            <>
              <h2 className="mb-4 text-xl font-semibold">Videos</h2>
              <div className="grid grid-cols-1 gap-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {displayVideos.map((video, index) => (
                  <div key={video.id} className="group relative">
                    <VideoCard
                      video={video}
                      className="w-full transition-transform duration-200 group-hover:scale-105"
                      onClick={() => dispatch(setCurrentVideoViewIndex(index))}
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {/* Media Viewer Modals */}
      {isImageViewOpen && <MediaView images={displayImages} />}
      {isVideoViewOpen && <VideoPlayerOverlay videos={displayVideos} />}
    </div>
  );
};
