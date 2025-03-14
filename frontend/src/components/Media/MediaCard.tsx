import React, { useState, useRef } from 'react';
import { MediaCardProps } from '@/types/Media';
import { Play, Volume2, VolumeX, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MediaCard({ item, type }: MediaCardProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleLoadComplete = () => {
    setIsLoading(false);
    setIsError(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setIsError(true);
  };

  const toggleMute = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (videoRef.current) {
      videoRef.current.muted = !videoRef.current.muted;
      setIsMuted(videoRef.current.muted);
    }
  };

  const handleMediaClick = () => {
    if (type === 'video' && videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play();
      } else {
        videoRef.current.pause();
      }
    }
  };

  return (
    <div
      className="group relative h-full w-full overflow-hidden rounded-xl shadow-sm transition-all duration-500 ease-out hover:-translate-y-1 hover:shadow-xl dark:bg-card dark:text-card-foreground"
      onClick={handleMediaClick}
      role={type === 'video' ? 'button' : 'img'}
      tabIndex={0}
      aria-label={`${type === 'video' ? 'Play' : 'View'} ${item.title}`}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/30 backdrop-blur-sm">
          <div className="animate-pulse-ring flex h-16 w-16 items-center justify-center rounded-full bg-blue-500/20">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        </div>
      )}

      {isError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/90">
          <p className="text-white">Failed to load media</p>
          <button
            className="mt-2 rounded-lg bg-blue-500 px-4 py-2 text-white shadow-lg transition-all hover:bg-blue-600 hover:shadow-blue-500/25"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      )}

      {type === 'image' ? (
        <img
          src={item.thumbnailUrl || item.url}
          alt={item.title}
          className={cn(
            'h-full w-full rounded-xl object-cover transition-all duration-700 ease-out group-hover:scale-105',
            isLoading && 'opacity-0',
            isError && 'hidden',
          )}
          onLoad={handleLoadComplete}
          onError={handleError}
        />
      ) : (
        <>
          <video
            ref={videoRef}
            src={item.url}
            className={cn(
              'h-full w-full rounded-xl object-cover transition-all duration-700 ease-out group-hover:scale-105',
              isLoading && 'opacity-0',
              isError && 'hidden',
            )}
            playsInline
            muted={isMuted}
            loop
            onLoadedData={handleLoadComplete}
            onError={handleError}
          />

          <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 backdrop-blur-sm transition-opacity duration-300 group-hover:opacity-100">
            <Play
              className="h-16 w-16 transform text-white drop-shadow-lg transition-transform duration-300 group-hover:scale-110"
              fill="white"
              strokeWidth={1.5}
            />
            <button
              className="rounded-full absolute bottom-4 right-4 bg-black/50 p-2 transition-colors duration-300 hover:bg-black/70"
              onClick={toggleMute}
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? (
                <VolumeX className="h-5 w-5 text-white" />
              ) : (
                <Volume2 className="h-5 w-5 text-white" />
              )}
            </button>
          </div>
        </>
      )}

      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      <div className="absolute bottom-0 left-0 w-full translate-y-full transform p-4 transition-transform duration-300 ease-out group-hover:translate-y-0">
        <div className="rounded-lg bg-black/70 p-3 backdrop-blur-sm">
          <h3 className="line-clamp-1 text-lg font-medium text-white">
            {item.title}
          </h3>
          <p className="mt-1 line-clamp-2 text-sm text-gray-300">
            {item?.original}
          </p>
        </div>
      </div>

      <div className="rounded-xl absolute inset-0 ring-0 ring-blue-500/50 ring-offset-2 ring-offset-transparent transition-all duration-300 group-focus-visible:ring-2" />
    </div>
  );
}
