import React from 'react';
import { Info, Heart, X, Folder, ListVideo } from 'lucide-react';

interface VideoViewerControlsProps {
  showInfo: boolean;
  onToggleInfo: () => void;
  onOpenFolder: () => void | Promise<void>;
  onToggleFavourite: () => void;
  isFavourite: boolean;
  autoPlayNext: boolean;
  onToggleAutoPlayNext: () => void;
  onClose: () => void;
}

/** Control buttons for the full-screen video viewer. */
export const VideoViewerControls: React.FC<VideoViewerControlsProps> = ({
  showInfo,
  onToggleInfo,
  onOpenFolder,
  onToggleFavourite,
  isFavourite,
  autoPlayNext,
  onToggleAutoPlayNext,
  onClose,
}) => {
  return (
    <div className="absolute top-4 right-4 z-50 flex items-center gap-3">
      <button
        onClick={onToggleInfo}
        className={`cursor-pointer rounded-full ${
          showInfo ? 'bg-indigo-500/70' : 'bg-black/50'
        } p-2.5 text-white/90 transition-all duration-200 hover:bg-black/20 hover:text-white hover:shadow-lg`}
        aria-label="Show Info"
        title="Show Info"
      >
        <Info className="h-5 w-5" />
      </button>

      <button
        onClick={onOpenFolder}
        className="cursor-pointer rounded-full bg-black/50 p-2.5 text-white/90 transition-all duration-200 hover:bg-black/20 hover:text-white hover:shadow-lg"
        aria-label="Open Folder"
        title="Open Folder"
      >
        <Folder className="h-5 w-5" />
      </button>

      <button
        onClick={onToggleFavourite}
        className={`cursor-pointer rounded-full p-2.5 text-white transition-all duration-300 ${
          isFavourite
            ? 'bg-rose-500/80 hover:bg-rose-600 hover:shadow-lg'
            : 'bg-black/50 hover:bg-black/20 hover:text-white hover:shadow-lg'
        }`}
        aria-label={
          isFavourite ? 'Remove from favourites' : 'Add to favourites'
        }
        title="Favourites"
      >
        <Heart className={`h-5 w-5 ${isFavourite ? 'fill-current' : ''}`} />
      </button>

      <button
        onClick={onToggleAutoPlayNext}
        aria-pressed={autoPlayNext}
        className={`flex cursor-pointer items-center gap-2 rounded-full px-4 py-2 text-white transition-all duration-200 hover:shadow-lg ${
          autoPlayNext
            ? 'bg-indigo-500/70 hover:bg-indigo-600/80'
            : 'bg-black/50 hover:bg-black/20'
        }`}
        aria-label="Toggle auto-play next"
        title="Auto-play next"
      >
        <ListVideo className="h-4 w-4" />
        <span className="text-sm font-medium">
          {autoPlayNext ? 'Auto-play On' : 'Auto-play'}
        </span>
      </button>

      <button
        onClick={onClose}
        className="ml-2 cursor-pointer rounded-full bg-black/50 p-2.5 text-white/90 transition-all duration-200 hover:bg-black/20 hover:text-white hover:shadow-lg"
        aria-label="Close"
        title="Close"
      >
        <X className="h-5 w-5" />
      </button>
    </div>
  );
};
