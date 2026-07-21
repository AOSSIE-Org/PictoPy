import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Film, Calendar, Clock, Monitor, Info } from 'lucide-react';
import { Video } from '@/types/Media';
import { formatDurationLabel } from '@/utils/durationUtils';

interface VideoInfoPanelProps {
  show: boolean;
  onClose: () => void;
  video: Video | null;
  currentIndex: number;
  totalVideos: number;
}

export const VideoInfoPanel: React.FC<VideoInfoPanelProps> = ({
  show,
  onClose,
  video,
  currentIndex,
  totalVideos,
}) => {
  const getFormattedDate = () => {
    if (video?.metadata?.date_created) {
      return new Date(video.metadata.date_created).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    }
    return 'Date not available';
  };

  const getVideoName = () => {
    if (!video) return 'Video';
    // Handle both Unix (/) and Windows (\) path separators
    return video.metadata?.name || video.path?.split(/[/\\]/).pop() || 'Video';
  };

  const duration = formatDurationLabel(video?.metadata?.duration);
  const width = video?.metadata?.width ?? 0;
  const height = video?.metadata?.height ?? 0;
  const resolution =
    width > 0 && height > 0 ? `${width} × ${height}` : 'Not available';

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ type: 'spring', stiffness: 260, damping: 25 }}
          className="absolute top-20 left-6 z-50 w-[350px] rounded-xl border border-white/10 bg-black/60 p-6 shadow-xl backdrop-blur-lg"
        >
          <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-xl font-medium text-white">Video Details</h3>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white"
              aria-label="Close info panel"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-4 text-sm">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Film className="h-5 w-5 text-blue-400" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-white/50">Name</p>
                <p
                  className="truncate font-medium text-white"
                  title={getVideoName()}
                >
                  {getVideoName()}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Calendar className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-white/50">Date</p>
                <p className="font-medium text-white">{getFormattedDate()}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Clock className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-white/50">Duration</p>
                <p className="font-medium text-white">
                  {duration ?? 'Not available'}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Monitor className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-white/50">Resolution</p>
                <p className="font-medium text-white">{resolution}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Info className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-white/50">Position</p>
                <p className="font-medium text-white">
                  {currentIndex + 1} of {totalVideos}
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
