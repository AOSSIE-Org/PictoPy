import React from 'react';
import {
  Info,
  ImageIcon,
  Folder,
  ExternalLink,
  Share2,
  Heart,
  Play,
  Pause,
  Lock,
  X,
} from 'lucide-react';

interface MediaViewControlsProps {
  showInfo: boolean;
  onToggleInfo: () => void;
  onToggleFavorite: () => void;
  isFavorite: boolean;
  isSlideshowActive: boolean;
  onToggleSlideshow: () => void;
  onClose: () => void;
  type?: string;
}

export const MediaViewControls: React.FC<MediaViewControlsProps> = ({
  showInfo,
  onToggleInfo,
  onToggleFavorite,
  isFavorite,
  isSlideshowActive,
  onToggleSlideshow,
  onClose,
  type = 'image',
}) => {
  return (
    <div className="absolute top-4 right-4 z-50 flex items-center gap-3">
      <button
        onClick={onToggleInfo}
        className={`rounded-full cursor-pointer ${
          showInfo ? 'bg-blue-500/70' : 'bg-white/10'
        } p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg`}
        aria-label="Show Info"
      >
        <Info className="h-5 w-5" />
      </button>

      <button
        className="cursor-pointer rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
        aria-label="Set as Wallpaper"
      >
        <ImageIcon className="h-5 w-5" />
      </button>

      <button
        className="cursor-pointer rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
        aria-label="Open Folder"
      >
        <Folder className="h-5 w-5" />
      </button>

      <button
        className="cursor-pointer rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
        aria-label="Open With"
      >
        <ExternalLink className="h-5 w-5" />
      </button>

      <button
        className="cursor-pointer rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
        aria-label="Share"
      >
        <Share2 className="h-5 w-5" />
      </button>

      <button
        onClick={onToggleFavorite}
        className={`cursor-pointer rounded-full p-2.5 text-white transition-all duration-300 ${
          isFavorite
            ? 'bg-rose-500/80 hover:bg-rose-600 hover:shadow-lg'
            : 'bg-white/10 hover:bg-white/20 hover:text-white hover:shadow-lg'
        }`}
        aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
      >
        <Heart className={`h-5 w-5 ${isFavorite ? 'fill-current' : ''}`} />
      </button>

      <button
        className="cursor-pointer rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
        aria-label="Move to Secure Folder"
      >
        <Lock className="h-5 w-5" />
      </button>

      {type === 'image' && (
        <button
          onClick={onToggleSlideshow}
          className="flex cursor-pointer items-center gap-2 rounded-full bg-indigo-500/70 px-4 py-2 text-white transition-all duration-200 hover:bg-indigo-600/80 hover:shadow-lg"
          aria-label="Toggle Slideshow"
        >
          {isSlideshowActive ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          <span className="text-sm font-medium">
            {isSlideshowActive ? 'Pause' : 'Slideshow'}
          </span>
        </button>
      )}

      <button
        onClick={onClose}
        className="ml-2 cursor-pointer rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
        aria-label="Close"
      >
        <X className="h-5 w-5" />
      </button>
    </div>
  );
};
