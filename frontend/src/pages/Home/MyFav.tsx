import { useEffect, useMemo, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { selectImages } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { Heart, Video, Play, Clock, X } from 'lucide-react';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import {
  fetchFavouriteVideos,
  VideoData,
  toggleVideoFavourite,
} from '@/api/api-functions/videos';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { convertFileSrc } from '@tauri-apps/api/core';
import NetflixStylePlayer from '@/components/VideoPlayer/NetflixStylePlayer';

// Format duration from seconds to MM:SS or HH:MM:SS
const formatDuration = (seconds?: number): string => {
  if (!seconds) return '00:00';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Video Card Component for Favourites
const FavouriteVideoCard = ({
  video,
  onClick,
  onToggleFavourite,
}: {
  video: VideoData;
  onClick: () => void;
  onToggleFavourite: () => void;
}) => {
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const videoSrc = convertFileSrc(video.path);

  return (
    <Card
      className="group cursor-pointer overflow-hidden transition-all hover:shadow-lg"
      onClick={onClick}
    >
      <CardContent className="p-0">
        <div className="relative aspect-video overflow-hidden bg-gray-900">
          {!videoError ? (
            <video
              src={videoSrc}
              className={`h-full w-full object-cover transition-transform duration-300 group-hover:scale-105 ${!videoLoaded ? 'opacity-0' : 'opacity-100'}`}
              muted
              playsInline
              preload="metadata"
              onLoadedMetadata={(e) => {
                const videoEl = e.currentTarget;
                const seekTime = Math.min(1, videoEl.duration * 0.1);
                videoEl.currentTime = seekTime;
              }}
              onSeeked={() => setVideoLoaded(true)}
              onError={() => {
                setVideoError(true);
                setVideoLoaded(true);
              }}
            />
          ) : null}
          {(!videoLoaded || videoError) && (
            <div className="absolute inset-0 flex h-full w-full items-center justify-center bg-gray-800">
              <Video className="h-12 w-12 text-gray-500" />
            </div>
          )}

          {/* Play overlay */}
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 transition-opacity group-hover:opacity-100">
            <div className="rounded-full bg-white/90 p-3">
              <Play className="h-8 w-8 fill-current text-gray-900" />
            </div>
          </div>

          {/* Duration badge */}
          {video.duration && (
            <div className="absolute bottom-2 right-2">
              <Badge
                variant="secondary"
                className="bg-black/70 text-xs text-white"
              >
                <Clock className="mr-1 h-3 w-3" />
                {formatDuration(video.duration)}
              </Badge>
            </div>
          )}

          {/* Favourite button */}
          <button
            className="absolute top-2 right-2 rounded-full bg-black/50 p-1.5 opacity-0 transition-opacity hover:bg-black/70 group-hover:opacity-100"
            onClick={(e) => {
              e.stopPropagation();
              onToggleFavourite();
            }}
          >
            <Heart className="h-4 w-4 fill-red-500 text-red-500" />
          </button>

          {/* Video badge */}
          <div className="absolute top-2 left-2">
            <Badge variant="secondary" className="bg-black/70 text-xs text-white">
              <Video className="mr-1 h-3 w-3" />
              Video
            </Badge>
          </div>
        </div>

        {/* Video info */}
        <div className="p-3">
          <h3 className="line-clamp-1 text-sm font-medium">
            {video.metadata?.name || 'Untitled Video'}
          </h3>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            {video.width && video.height && (
              <span>
                {video.width}x{video.height}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};


// Video Player Modal
const VideoPlayerModal = ({
  video,
  onClose,
}: {
  video: VideoData;
  onClose: () => void;
}) => {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/95"
      onClick={onClose}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-4 right-4 z-10 text-white hover:bg-white/20"
        onClick={onClose}
      >
        <X className="h-6 w-6" />
      </Button>

      <div className="mx-4 w-full max-w-5xl" onClick={(e) => e.stopPropagation()}>
        <NetflixStylePlayer
          videoSrc={convertFileSrc(video.path)}
          title={video.metadata?.name || 'Video'}
          description=""
        />
        <div className="mt-4 text-white">
          <h2 className="text-xl font-semibold">{video.metadata?.name}</h2>
          <div className="mt-2 flex items-center gap-4 text-sm text-gray-400">
            {video.duration && <span>{formatDuration(video.duration)}</span>}
            {video.width && video.height && (
              <span>
                {video.width}x{video.height}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export const MyFav = () => {
  const dispatch = useDispatch();
  const images = useSelector(selectImages);
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const [favouriteVideos, setFavouriteVideos] = useState<VideoData[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoData | null>(null);
  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;

  // Fetch images
  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
    enabled: !isSearchActive,
  });

  // Fetch favourite videos
  const {
    data: videosData,
    isLoading: videosLoading,
    refetch: refetchVideos,
  } = usePictoQuery({
    queryKey: ['favouriteVideos'],
    queryFn: () => fetchFavouriteVideos(),
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading favourites',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load favourites. Please try again later.',
    },
  );

  // Handle images fetching
  useEffect(() => {
    if (!isSearchActive && isSuccess) {
      const images = data?.data as Image[];
      dispatch(setImages(images));
    }
  }, [data, isSuccess, dispatch, isSearchActive]);

  // Handle videos fetching
  useEffect(() => {
    if (videosData?.data) {
      setFavouriteVideos(videosData.data);
    }
  }, [videosData]);

  const favouriteImages = useMemo(
    () => images.filter((image) => image.isFavourite === true),
    [images],
  );

  const handleToggleVideoFavourite = async (videoId: string) => {
    try {
      await toggleVideoFavourite(videoId);
      // Remove from local state immediately
      setFavouriteVideos((prev) => prev.filter((v) => v.id !== videoId));
    } catch (err) {
      console.error('Failed to toggle favourite:', err);
    }
  };

  // If a video is selected, show the player
  if (selectedVideo) {
    return (
      <VideoPlayerModal
        video={selectedVideo}
        onClose={() => setSelectedVideo(null)}
      />
    );
  }

  const hasNoFavourites =
    favouriteImages.length === 0 && favouriteVideos.length === 0;

  if (hasNoFavourites && !isLoading && !videosLoading) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold">Favourites</h1>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="bg-muted/50 mb-6 flex h-32 w-32 items-center justify-center rounded-full">
            <Heart className="h-16 w-16 text-muted-foreground" />
          </div>
          <h2 className="text-foreground mb-3 text-xl font-semibold">
            No Favourites Yet
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Start building your collection by marking images and videos as
            favourites. Click the heart icon on any item to add it here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-full flex-col pr-6">
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        {/* Favourite Videos Section */}
        {favouriteVideos.length > 0 && (
          <div className="mb-8">
            <div className="mb-4 flex items-center gap-2">
              <Video className="h-5 w-5 text-primary" />
              <h2 className="text-xl font-semibold">Favourite Videos</h2>
              <span className="text-sm text-muted-foreground">
                ({favouriteVideos.length})
              </span>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {favouriteVideos.map((video) => (
                <FavouriteVideoCard
                  key={video.id}
                  video={video}
                  onClick={() => setSelectedVideo(video)}
                  onToggleFavourite={() => handleToggleVideoFavourite(video.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Favourite Images Section */}
        {favouriteImages.length > 0 && (
          <ChronologicalGallery
            images={favouriteImages}
            showTitle={true}
            title={`Favourite Images (${favouriteImages.length})`}
            onMonthOffsetsChange={setMonthMarkers}
            scrollContainerRef={scrollableRef}
          />
        )}
      </div>

      {/* Timeline Scrollbar */}
      {monthMarkers.length > 0 && (
        <TimelineScrollbar
          scrollableRef={scrollableRef}
          monthMarkers={monthMarkers}
          className="absolute top-0 right-0 h-full w-4"
        />
      )}
    </div>
  );
};
