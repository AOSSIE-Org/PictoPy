import { useEffect, useState } from 'react';
import { Video, Play, Clock, Heart, X, Sparkles } from 'lucide-react';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllVideos, toggleVideoFavourite, VideoData } from '@/api/api-functions/videos';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
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

interface VideoCardProps {
  video: VideoData;
  onClick: () => void;
  onToggleFavourite: () => void;
}

const VideoCard = ({ video, onClick, onToggleFavourite }: VideoCardProps) => {
  const [imageError, setImageError] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [videoError, setVideoError] = useState(false);

  const videoSrc = convertFileSrc(video.path);
  const hasThumbnail = video.thumbnailPath && video.thumbnailPath.length > 0 && !imageError;

  return (
    <Card 
      className="group overflow-hidden transition-all hover:shadow-lg cursor-pointer"
      onClick={onClick}
    >
      <CardContent className="p-0">
        <div className="relative aspect-video overflow-hidden bg-gray-900">
          {hasThumbnail ? (
            <img
              src={convertFileSrc(video.thumbnailPath)}
              alt={video.metadata?.name || 'Video thumbnail'}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              onError={() => setImageError(true)}
            />
          ) : (
            <>
              {/* Use video element to show first frame as thumbnail */}
              {!videoError ? (
                <video
                  src={videoSrc}
                  className={`h-full w-full object-cover transition-transform duration-300 group-hover:scale-105 ${!videoLoaded ? 'opacity-0' : 'opacity-100'}`}
                  muted
                  playsInline
                  preload="metadata"
                  onLoadedMetadata={(e) => {
                    const videoEl = e.currentTarget;
                    // Seek to 1 second or 10% of duration, whichever is smaller
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
            </>
          )}
          
          {/* Play overlay */}
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 transition-opacity group-hover:opacity-100">
            <div className="rounded-full bg-white/90 p-3">
              <Play className="h-8 w-8 text-gray-900 fill-current" />
            </div>
          </div>

          {/* Duration badge */}
          {video.duration && (
            <div className="absolute bottom-2 right-2">
              <Badge variant="secondary" className="bg-black/70 text-white text-xs">
                <Clock className="mr-1 h-3 w-3" />
                {formatDuration(video.duration)}
              </Badge>
            </div>
          )}

          {/* Favourite button */}
          <button
            className="absolute top-2 right-2 p-1.5 rounded-full bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
            onClick={(e) => {
              e.stopPropagation();
              onToggleFavourite();
            }}
          >
            <Heart 
              className={`h-4 w-4 ${video.isFavourite ? 'text-red-500 fill-red-500' : 'text-white'}`} 
            />
          </button>
        </div>

        {/* Video info */}
        <div className="p-3">
          <h3 className="text-sm font-medium line-clamp-1">
            {video.metadata?.name || 'Untitled Video'}
          </h3>
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            {video.width && video.height && (
              <span>{video.width}x{video.height}</span>
            )}
            {video.metadata?.date_created && (
              <span>
                {new Date(video.metadata.date_created).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const VideoCardSkeleton = () => (
  <Card className="overflow-hidden">
    <CardContent className="p-0">
      <Skeleton className="aspect-video w-full" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </CardContent>
  </Card>
);

const EmptyVideosState = () => (
  <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4">
    <div className="rounded-full bg-primary/10 p-6 mb-4">
      <Video className="h-12 w-12 text-primary" />
    </div>
    <h2 className="text-2xl font-semibold mb-2">No Videos Yet</h2>
    <p className="text-muted-foreground max-w-md">
      Add folders containing videos to see them here. Supported formats include MP4, MOV, AVI, MKV, and WebM.
    </p>
  </div>
);

const VideoPlayerModal = ({ 
  video, 
  onClose 
}: { 
  video: VideoData; 
  onClose: () => void;
}) => {
  return (
    <div 
      className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center"
      onClick={onClose}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-4 right-4 text-white hover:bg-white/20 z-10"
        onClick={onClose}
      >
        <X className="h-6 w-6" />
      </Button>
      
      <div 
        className="w-full max-w-5xl mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <NetflixStylePlayer
          videoSrc={convertFileSrc(video.path)}
          title={video.metadata?.name || 'Video'}
          description=""
        />
        <div className="mt-4 text-white">
          <h2 className="text-xl font-semibold">{video.metadata?.name}</h2>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
            {video.duration && <span>{formatDuration(video.duration)}</span>}
            {video.width && video.height && <span>{video.width}x{video.height}</span>}
            {video.metadata?.codec && <span>{video.metadata.codec.toUpperCase()}</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

const Videos = () => {
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoData | null>(null);

  const { data, isLoading, isSuccess, isError, error, refetch } = usePictoQuery({
    queryKey: ['videos'],
    queryFn: () => fetchAllVideos(),
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading videos',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load videos. Please try again later.',
    },
  );

  useEffect(() => {
    if (isSuccess && data?.data) {
      setVideos(data.data);
    }
  }, [data, isSuccess]);

  const handleToggleFavourite = async (videoId: string) => {
    try {
      await toggleVideoFavourite(videoId);
      // Update local state
      setVideos(prev => 
        prev.map(v => 
          v.id === videoId ? { ...v, isFavourite: !v.isFavourite } : v
        )
      );
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

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="mb-6 pr-6">
        <div className="flex items-center gap-2 mb-2">
          <Video className="h-6 w-6 text-primary" />
          <h1 className="text-3xl font-bold">Videos</h1>
        </div>
        <p className="text-muted-foreground">
          Browse and play your video collection
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto hide-scrollbar pr-6">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <VideoCardSkeleton key={i} />
            ))}
          </div>
        ) : videos.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-6">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                onClick={() => setSelectedVideo(video)}
                onToggleFavourite={() => handleToggleFavourite(video.id)}
              />
            ))}
          </div>
        ) : (
          <EmptyVideosState />
        )}
      </div>
    </div>
  );
};

export default Videos;
