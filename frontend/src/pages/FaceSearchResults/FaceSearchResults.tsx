import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { convertFileSrc } from '@tauri-apps/api/core';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { VideoCard } from '@/components/Media/VideoCard';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';
import { Button } from '@/components/ui/button';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import {
  setCurrentViewIndex as setCurrentVideoViewIndex,
  setVideos,
} from '@/features/videoSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { selectIsVideoViewOpen, selectVideos } from '@/features/videoSelectors';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import {
  fetchSearchedFaces,
  fetchSearchedFacesBase64,
  type FaceSearchResponse,
} from '@/api/api-functions';
import { getErrorMessage } from '@/lib/utils';
import { ROUTES } from '@/constants/routes';
import { RootState } from '@/app/store';

export const FaceSearchResults = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const queryImage = useSelector((state: RootState) => state.search.queryImage);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const displayImages = useSelector(selectImages);
  const isVideoViewOpen = useSelector(selectIsVideoViewOpen);
  const displayVideos = useSelector(selectVideos);

  const { data, isLoading, isSuccess, isError, error, errorMessage } =
    usePictoQuery({
      queryKey: ['face-search', queryImage],
      queryFn: async (): Promise<FaceSearchResponse> => {
        // Webcam captures arrive as a data URL, uploaded files as a path.
        if (queryImage!.startsWith('data:')) {
          return fetchSearchedFacesBase64({ base64_data: queryImage! });
        }
        return fetchSearchedFaces({ path: queryImage! });
      },
      enabled: !!queryImage,
      retry: false,
      gcTime: 0,
    });

  // Nothing to search for (e.g. the chip was cleared or the app was reloaded
  // on this URL), so there is nothing to show here.
  useEffect(() => {
    if (!queryImage) {
      navigate(`/${ROUTES.HOME}`, { replace: true });
    }
  }, [queryImage, navigate]);

  useEffect(() => {
    if (isLoading) {
      dispatch(showLoader('Searching faces...'));
    } else if (isSuccess && data) {
      dispatch(setImages(data.data ?? []));
      dispatch(setVideos(data.videos ?? []));
      dispatch(hideLoader());
    } else if (isError) {
      dispatch(hideLoader());
    }

    return () => {
      dispatch(hideLoader());
    };
  }, [data, isLoading, isSuccess, isError, dispatch]);

  const thumbnailSrc = queryImage
    ? queryImage.startsWith('data:')
      ? queryImage
      : convertFileSrc(queryImage)
    : undefined;

  const searchError = isError
    ? getErrorMessage(error, errorMessage) ||
      'There was an error while searching for faces.'
    : null;

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
      <h1 className="mb-6 flex items-center gap-3 text-2xl font-bold">
        Results for
        {thumbnailSrc && (
          <img
            src={thumbnailSrc}
            alt="Searched face"
            className="h-10 w-10 rounded-full object-cover"
          />
        )}
      </h1>

      {searchError ? (
        <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
          <AlertCircle className="text-destructive mb-4 h-12 w-12" />
          <h3 className="text-destructive mb-2 text-xl font-medium">
            Search Failed
          </h3>
          <p>{searchError}</p>
        </div>
      ) : (
        isSuccess && (
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
                        onClick={() =>
                          dispatch(setCurrentVideoViewIndex(index))
                        }
                      />
                    </div>
                  ))}
                </div>
              </>
            )}

            {displayImages.length === 0 && displayVideos.length === 0 && (
              <div className="text-muted-foreground flex flex-col items-center justify-center py-12">
                <p>No matching faces found in your gallery for this photo.</p>
              </div>
            )}
          </>
        )
      )}

      {isImageViewOpen && <MediaView images={displayImages} />}
      {isVideoViewOpen && <VideoPlayerOverlay videos={displayVideos} />}
    </div>
  );
};
