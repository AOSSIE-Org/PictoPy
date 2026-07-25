import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Film, Calendar, Clock, Monitor, Info, Tag } from 'lucide-react';
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
  const tags = video?.tags ?? [];

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ type: 'spring', stiffness: 260, damping: 25 }}
          className="absolute top-20 left-6 z-50 w-[350px] rounded-xl border border-black/10 bg-white/80 p-6 shadow-xl backdrop-blur-lg dark:border-white/10 dark:bg-black/60"
        >
          <div className="mb-4 flex items-center justify-between border-b border-black/10 pb-3 dark:border-white/10">
            <h3 className="text-xl font-medium text-gray-900 dark:text-white">
              Video Details
            </h3>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-900 dark:text-white/70 dark:hover:text-white"
              aria-label="Close info panel"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-4 text-sm">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                <Film className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-gray-500 dark:text-white/50">Name</p>
                <p
                  className="truncate font-medium text-gray-900 dark:text-white"
                  title={getVideoName()}
                >
                  {getVideoName()}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                <Calendar className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-white/50">Date</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {getFormattedDate()}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                <Clock className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-white/50">
                  Duration
                </p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {duration ?? 'Not available'}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                <Monitor className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-white/50">
                  Resolution
                </p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {resolution}
                </p>
              </div>
            </div>

            {tags.length > 0 && (
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                  <Tag className="h-5 w-5 text-rose-600 dark:text-rose-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-gray-500 dark:text-white/50">
                    Tags
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {tags.map((tag, index) => (
                      <span
                        key={`${tag}-${index}`}
                        className="rounded-full border border-black/20 px-2 py-0.5 text-xs text-gray-800 dark:border-white/30 dark:text-white"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-white/50">
                  Position
                </p>
                <p className="font-medium text-gray-900 dark:text-white">
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
