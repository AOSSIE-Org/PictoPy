import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { convertFileSrc } from '@tauri-apps/api/core';
import NetflixStylePlayer from '@/components/VideoPlayer/NetflixStylePlayer';
import { formatDuration } from '@/utils/formatDuration';
import { VideoData } from '@/api/api-functions/videos';

interface VideoPlayerModalProps {
  video: VideoData;
  onClose: () => void;
}

export const VideoPlayerModal = ({ video, onClose }: VideoPlayerModalProps) => {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/95"
      onClick={onClose}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute right-4 top-4 z-10 text-white hover:bg-white/20"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
      >
        <X className="h-6 w-6" />
      </Button>

      <div
        className="mx-4 w-full max-w-5xl"
        onClick={(e) => e.stopPropagation()}
      >
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
            {video.metadata?.codec && (
              <span>{video.metadata.codec.toUpperCase()}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayerModal;
