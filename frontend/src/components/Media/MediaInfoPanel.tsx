import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { open } from '@tauri-apps/plugin-shell';
import {
  X,
  ImageIcon as ImageLucide,
  Calendar,
  MapPin,
  Tag,
  Info,
  SquareArrowOutUpRight,
} from 'lucide-react';
import { Image } from '@/types/Media';

interface MediaInfoPanelProps {
  show: boolean;
  onClose: () => void;
  currentImage: Image | null;
  currentIndex: number;
  totalImages: number;
}

export const MediaInfoPanel: React.FC<MediaInfoPanelProps> = ({
  show,
  onClose,
  currentImage,
  currentIndex,
  totalImages,
}) => {
  const getFormattedDate = () => {
    if (currentImage?.metadata?.date_created) {
      return new Date(currentImage.metadata.date_created).toLocaleDateString(
        'en-US',
        {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        },
      );
    }
    return 'Date not available';
  };

  const getImageName = () => {
    if (!currentImage) return 'Image';
    // Handle both Unix (/) and Windows (\) path separators
    return currentImage.path?.split(/[/\\]/).pop() || 'Image';
  };

  const handleLocationClick = async () => {
    if (currentImage?.metadata?.latitude && currentImage?.metadata?.longitude) {
      const { latitude, longitude } = currentImage.metadata;
      try {
        await open(`https://maps.google.com/?q=${latitude},${longitude}`);
      } catch (error) {
        console.error('Failed to open map URL:', error);
      }
    }
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ type: 'spring', stiffness: 260, damping: 25 }}
          className="absolute top-10 left-6 z-50 w-[350px] rounded-xl border border-black/10 bg-white/80 p-6 shadow-xl backdrop-blur-lg dark:border-white/10 dark:bg-black/60"
        >
          <div className="mb-4 flex items-center justify-between border-b border-black/10 pb-3 dark:border-white/10">
            <h3 className="text-xl font-medium text-gray-900 dark:text-white">
              Image Details
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
                <ImageLucide className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-gray-500 dark:text-white/50">Name</p>
                <p
                  className="truncate font-medium text-gray-900 dark:text-white"
                  title={getImageName()}
                >
                  {getImageName()}
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
                <MapPin className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-gray-500 dark:text-white/50">
                  Location
                </p>
                {currentImage?.metadata?.latitude &&
                currentImage?.metadata?.longitude ? (
                  <button
                    type="button"
                    onClick={handleLocationClick}
                    className="flex w-full items-center truncate text-left font-medium text-gray-900 hover:underline dark:text-white"
                  >
                    {`Lat: ${currentImage.metadata.latitude.toFixed(4)}, Lon: ${currentImage.metadata.longitude.toFixed(4)}`}
                    <SquareArrowOutUpRight className="ml-1 h-[14px] w-[14px]" />
                  </button>
                ) : (
                  <p className="font-medium text-gray-900 dark:text-white">
                    Location not available
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                <Tag className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="mb-1 text-xs text-gray-500 dark:text-white/50">
                  Tags
                </p>
                {currentImage?.tags?.length ? (
                  <div className="flex flex-wrap gap-2">
                    {currentImage.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="rounded-full border border-blue-500/30 bg-blue-500/20 px-2 py-1 text-xs text-blue-600 dark:text-blue-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-white/60">
                    No tags available
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-black/5 p-2 dark:bg-white/10">
                <Info className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-white/50">
                  Position
                </p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {currentIndex + 1} of {totalImages}
                </p>
              </div>
            </div>

            <div className="mt-4 border-t border-black/10 pt-3 dark:border-white/10">
              <button
                className="w-full rounded-lg bg-black/5 py-2 text-gray-900 hover:bg-black/10 dark:bg-white/10 dark:text-white dark:hover:bg-white/20"
                onClick={(e) => {
                  e.preventDefault();
                  // Button disabled - does nothing
                }}
              >
                Open Original File
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
