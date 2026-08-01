import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AxiosError } from 'axios';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { VideoCard } from '@/components/Media/VideoCard';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';
import { Cluster, Image, ScoredImage, ScoredVideo, Video } from '@/types/Media';
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
  fetchAllClusters,
  fetchMultiPersonSearch,
  SemanticSearchAPIResponse,
  SemanticSearchVideosAPIResponse,
} from '@/api/api-functions';
import { APIResponse } from '@/types/API';
import { getErrorMessage } from '@/lib/utils';
import { isSemanticSearchAvailable } from '@/types/models';
import { useNavigate, useSearchParams } from 'react-router';
import { ROUTES } from '@/constants/routes';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, AlertCircle, Users } from 'lucide-react';
import { resolvePeopleQuery } from '@/utils/peopleQuery';
import { formatPeopleTitle, getPersonName } from '@/utils/personUtils';

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
  const [peopleSearchError, setPeopleSearchError] = useState<string | null>(
    null,
  );

  const { data: statusData, isSuccess: isStatusSuccess } = usePictoQuery({
    queryKey: ['models', 'status'],
    queryFn: fetchModelStatus,
  });

  // Named clusters are needed before the query can be classified, so the
  // tag/semantic searches wait on them rather than racing a people search.
  const {
    data: clustersData,
    isSuccess: isClustersSuccess,
    isError: isClustersError,
  } = usePictoQuery({
    queryKey: ['clusters'],
    queryFn: fetchAllClusters,
    enabled: !!query,
  });

  const clustersSettled = isClustersSuccess || isClustersError;

  const peopleQuery = useMemo(() => {
    // An explicit mode=tag/semantic is the user opting out of people search.
    if (!clustersSettled || mode !== 'auto') return null;
    const clusters = (clustersData?.data?.clusters ?? []) as Cluster[];
    return resolvePeopleQuery(query, clusters);
  }, [query, mode, clustersData, clustersSettled]);

  const isPeopleQuery = peopleQuery !== null;

  const peopleClusterIds = useMemo(
    () => peopleQuery?.matched.map((cluster) => cluster.cluster_id) ?? [],
    [peopleQuery],
  );

  const {
    data: peopleData,
    isLoading: isPeopleLoading,
    isSuccess: isPeopleSuccess,
    isError: isPeopleError,
    error: peopleError,
    errorMessage: peopleErrorMessage,
  } = usePictoQuery({
    queryKey: ['people-search', peopleClusterIds, peopleQuery?.matchMode],
    queryFn: () =>
      fetchMultiPersonSearch({
        cluster_ids: peopleClusterIds,
        match_mode: peopleQuery!.matchMode,
      }),
    enabled: isPeopleQuery,
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
      enabled: !!query && clustersSettled && !isPeopleQuery,
    });

  // Videos run as their own query: they share the mode logic but a video
  // failure (e.g. no frames embedded yet) must not blank the image results,
  // and vice versa.
  const {
    data: videoData,
    isSuccess: isVideoSuccess,
    isError: isVideoError,
    error: videoError,
    errorMessage: videoErrorMessage,
  } = usePictoQuery({
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

      // Reuse the status already fetched above; only fetch again if it
      // hasn't resolved yet, avoiding a redundant round-trip per search.
      let semAvailable = semanticAvailable;
      if (!isStatusSuccess) {
        const statusRes = await fetchModelStatus();
        semAvailable =
          statusRes.success && statusRes.data
            ? isSemanticSearchAvailable(statusRes.data)
            : false;
      }

      if (semAvailable) {
        const semResponse = await semanticSearchVideos({ query });
        return { ...semResponse, resultType: 'semantic' };
      }

      return { ...tagResponse, resultType: 'tag' };
    },
    enabled: !!query && clustersSettled && !isPeopleQuery,
  });

  useEffect(() => {
    if (!isVideoSuccess || !videoData) return;

    const fetchedVideos: Video[] =
      videoData.resultType === 'semantic'
        ? ((videoData.data?.videos ?? []) as ScoredVideo[])
        : ((videoData.data ?? []) as Video[]);

    dispatch(setVideos(fetchedVideos));
  }, [videoData, isVideoSuccess, dispatch]);

  // A failed video search should not be silent; surface it in the logs like
  // the image query's error branch does.
  useEffect(() => {
    if (isVideoError) {
      console.error(
        'Video search failed:',
        getErrorMessage(videoError, videoErrorMessage),
      );
    }
  }, [isVideoError, videoError, videoErrorMessage]);

  const videoSearchError = isVideoError
    ? getErrorMessage(videoError, videoErrorMessage) ||
      'Failed to search videos'
    : null;

  const effectiveMode = data?.resultType || mode;

  useEffect(() => {
    if (!isPeopleQuery) return;

    if (isPeopleLoading) {
      setPeopleSearchError(null);
      dispatch(showLoader('Searching people'));
    } else if (isPeopleError) {
      setPeopleSearchError(
        getErrorMessage(peopleError, peopleErrorMessage) ||
          'Failed to search for people',
      );
      dispatch(hideLoader());
    } else if (isPeopleSuccess) {
      setPeopleSearchError(null);
      const images = (peopleData?.data?.images ?? []) as Array<
        Partial<Image> & { id: string; path: string }
      >;
      dispatch(
        setImages(
          images.map((img) => ({
            id: img.id,
            path: img.path,
            thumbnailPath: img.thumbnailPath || '',
            metadata: img.metadata,
            folder_id: '',
            isTagged: true,
          })) as Image[],
        ),
      );
      dispatch(hideLoader());
    }

    return () => {
      dispatch(hideLoader());
    };
  }, [
    isPeopleQuery,
    peopleData,
    isPeopleLoading,
    isPeopleSuccess,
    isPeopleError,
    peopleError,
    peopleErrorMessage,
    dispatch,
  ]);

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

      {peopleQuery && (
        <div className="border-primary/20 bg-primary/5 mb-4 rounded-lg border px-4 py-2.5">
          <div className="flex flex-wrap items-center gap-2">
            <Users className="text-muted-foreground h-4 w-4 shrink-0" />
            <span className="text-muted-foreground text-sm">
              {peopleQuery.matchMode === 'match_any'
                ? 'Photos with any of:'
                : 'Photos with all of:'}
            </span>
            {peopleQuery.matched.map((cluster) => (
              <Badge
                key={cluster.cluster_id}
                variant="secondary"
                className="text-xs"
              >
                {getPersonName(cluster)}
              </Badge>
            ))}
          </div>
          {peopleQuery.unmatched.length > 0 && (
            <p className="text-muted-foreground mt-1.5 text-xs">
              No one is named{' '}
              {formatPeopleTitle(peopleQuery.unmatched, 'match_all')} — that
              part of your search was ignored.
            </p>
          )}
        </div>
      )}

      {isPeopleQuery ? (
        <div className="mb-4">
          <Button
            variant="outline"
            size="sm"
            className="hover:bg-accent cursor-pointer rounded-full text-xs"
            onClick={() =>
              navigate(
                `/${ROUTES.SEARCH}?value=${encodeURIComponent(query)}&mode=tag`,
              )
            }
          >
            Search this as text instead
          </Button>
        </div>
      ) : (
        isSuccess &&
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
        )
      )}

      {!query ? (
        <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
          <p>Please enter a search term to find photos and videos.</p>
        </div>
      ) : isPeopleQuery ? (
        // People search is face-cluster backed, so it covers photos only.
        peopleSearchError ? (
          <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
            <AlertCircle className="text-destructive mb-4 h-12 w-12" />
            <h3 className="text-destructive mb-2 text-xl font-medium">
              Search Failed
            </h3>
            <p>{peopleSearchError}</p>
          </div>
        ) : displayImages.length > 0 ? (
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
        ) : (
          isPeopleSuccess && (
            <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
              <p>
                {peopleQuery?.matchMode === 'match_all'
                  ? 'No photos found with all of these people in them.'
                  : 'No photos found with these people in them.'}
              </p>
            </div>
          )
        )
      ) : searchError && videoSearchError ? (
        // Only a total failure (both media types) takes over the whole view.
        <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
          <AlertCircle className="text-destructive mb-4 h-12 w-12" />
          <h3 className="text-destructive mb-2 text-xl font-medium">
            Search Failed
          </h3>
          <p>{searchError}</p>
        </div>
      ) : (
        <>
          {/* Photos: an image-search error is shown inline so it never hides
              successfully-fetched videos. */}
          {searchError ? (
            <div className="text-muted-foreground mb-6 flex items-center gap-2 text-sm">
              <AlertCircle className="text-destructive h-4 w-4 shrink-0" />
              <span>Couldn't load photo results: {searchError}</span>
            </div>
          ) : (
            displayImages.length > 0 && (
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
            )
          )}

          {/* Videos: symmetric — a video-search error is inline and never
              hides successfully-fetched photos. */}
          {videoSearchError ? (
            <div className="text-muted-foreground mb-6 flex items-center gap-2 text-sm">
              <AlertCircle className="text-destructive h-4 w-4 shrink-0" />
              <span>Couldn't load video results: {videoSearchError}</span>
            </div>
          ) : (
            displayVideos.length > 0 && (
              <>
                <h2 className="mb-4 text-xl font-semibold">Videos</h2>
                <div className="grid grid-cols-1 gap-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                  {displayVideos.map((video, index) => (
                    <div key={video.id} className="group relative">
                      <VideoCard
                        video={video}
                        className="w-full transition-transform duration-200 group-hover:scale-105"
                        onClick={() =>
                          dispatch(setCurrentVideoViewIndex(index))
                        }
                      />
                    </div>
                  ))}
                </div>
              </>
            )
          )}

          {/* Both searches succeeded but nothing matched. */}
          {!searchError &&
            !videoSearchError &&
            isSuccess &&
            isVideoSuccess &&
            displayImages.length === 0 &&
            displayVideos.length === 0 && (
              <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
                {effectiveMode === 'semantic' ? (
                  <p>No matches found. Try describing it differently.</p>
                ) : (
                  <p>No photos or videos found matching your search.</p>
                )}
              </div>
            )}
        </>
      )}

      {/* Media Viewer Modals */}
      {isImageViewOpen && <MediaView images={displayImages} />}
      {isVideoViewOpen && <VideoPlayerOverlay videos={displayVideos} />}
    </div>
  );
};
