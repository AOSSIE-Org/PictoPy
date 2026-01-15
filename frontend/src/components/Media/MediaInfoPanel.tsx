import React from 'react';
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
import { cn } from '@/lib/utils';

interface MediaInfoPanelProps {
  show: boolean;
  onClose: () => void;
  currentImage: Image | null;
  currentIndex: number;
  totalImages: number;
  className?: string;
}

export const MediaInfoPanel: React.FC<MediaInfoPanelProps> = ({
  show,
  onClose,
  currentImage,
  currentIndex,
  totalImages,
  className,
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
      const url = `https://maps.google.com/?q=${latitude},${longitude}`;
      try {
        await open(url);
      } catch (error) {
        console.error('Failed to open map URL:', error);
      }
    }
  };

  if (!show) return null;

  return (
    <div className={cn("animate-in slide-in-from-left absolute top-10 left-6 z-50 w-[350px] rounded-xl border border-white/10 bg-black/60 p-6 shadow-xl backdrop-blur-lg transition-all duration-300", className)}>
      <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
        <h3 className="text-xl font-medium text-white">Image Details</h3>
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
            <ImageLucide className="h-5 w-5 text-blue-400" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-white/50">Name</p>
            <p
              className="truncate font-medium text-white"
              title={getImageName()}
            >
              {getImageName()}
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
            <MapPin className="h-5 w-5 text-red-400" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-white/50">Location</p>
            {currentImage?.metadata?.latitude &&
              currentImage?.metadata?.longitude ? (
              <button
                type="button"
                onClick={handleLocationClick}
                className="flex w-full cursor-pointer items-center truncate text-left font-medium text-white hover:underline"
                title={`Lat: ${currentImage.metadata.latitude}, Lon: ${currentImage.metadata.longitude}`}
              >
                {`Lat: ${currentImage.metadata.latitude.toFixed(4)}, Lon: ${currentImage.metadata.longitude.toFixed(4)}`}
                <SquareArrowOutUpRight className="ml-1 h-[14px] w-[14px]" />
              </button>
            ) : (
              <p className="font-medium text-white">Location not available</p>
            )}
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-white/10 p-2">
            <Tag className="h-5 w-5 text-purple-400" />
          </div>
          <div className="flex-1">
            <p className="mb-1 text-xs text-white/50">Tags</p>
            {currentImage?.tags && currentImage.tags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {currentImage.tags.map((tag, i) => (
                  <span
                    key={i}
                    className="rounded-full border border-blue-500/30 bg-blue-500/20 px-2 py-1 text-xs text-blue-300"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-white/60">No tags available</p>
            )}
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-white/10 p-2">
            <Info className="h-5 w-5 text-amber-400" />
          </div>
          <div>
            <p className="text-xs text-white/50">Position</p>
            <p className="font-medium text-white">
              {currentIndex + 1} of {totalImages}
            </p>
          </div>
        </div>

        <div className="mt-4 border-t border-white/10 pt-3">
          <button
            className="w-full cursor-pointer rounded-lg bg-white/10 py-2 text-white transition-colors hover:bg-white/20"
            onClick={async () => {
              if (currentImage?.path) {
                try {
                  await open(currentImage.path);
                } catch (error) {
                  console.error('Failed to open file:', error);
                }
              }
            }}
          >
            Open Original File
          </button>
        </div>
      </div>
    </div>
  );
};
