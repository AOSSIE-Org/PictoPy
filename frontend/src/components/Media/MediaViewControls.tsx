import React, { useState } from 'react';
import { Info, Heart, Play, Pause, X, Folder } from 'lucide-react';

interface MediaViewControlsProps {
  showInfo: boolean;
  onToggleInfo: () => void;
  onToggleFavourite: () => void;
  onOpenFolder: () => Promise<void>;
  isFavourite: boolean;
  isSlideshowActive: boolean;
  onToggleSlideshow: () => void;
  onClose: () => void;
  type?: string;
  duration: number;
  onDurationChange: (duration: number) => void;
}

// snap points in ms, mapped to a 0-2 slider scale
const DURATION_STEPS = [2000, 5000, 10000];

/** Control buttons for the full-screen media viewer. */
export const MediaViewControls: React.FC<MediaViewControlsProps> = ({
  showInfo,
  onToggleInfo,
  onToggleFavourite,
  onOpenFolder,
  isFavourite,
  isSlideshowActive,
  onToggleSlideshow,
  onClose,
  type = 'image',
  duration,
  onDurationChange,
}) => {
  const [showSettings, setShowSettings] = useState(false);

  // convert current duration (ms) to a step index (0,1,2) for the slider
  const currentStepIndex = DURATION_STEPS.indexOf(duration);
  const sliderValue = currentStepIndex === -1 ? 0 : currentStepIndex;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const stepIndex = Number(e.target.value);
    onDurationChange(DURATION_STEPS[stepIndex]);
  };

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

      {type === 'image' && (
        <div
          className="relative"
          onMouseEnter={() => setShowSettings(true)}
          onMouseLeave={() => setShowSettings(false)}
          onFocus={() => setShowSettings(true)}
          onBlur={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget as Node)) {
              setShowSettings(false);
            }
          }}
        >
          <button
            onClick={onToggleSlideshow}
            className="flex cursor-pointer items-center gap-2 rounded-full bg-indigo-500/70 px-4 py-2 text-white transition-all duration-200 hover:bg-indigo-600/80 hover:shadow-lg"
            aria-label="Toggle Slideshow"
            title="SlideShow"
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

          {showSettings && (
            <div className="absolute top-full left-1/2 -translate-x-1/2 pt-2">
              <div className="flex w-fit items-center gap-3 rounded-md border border-white/20 bg-black/85 px-3 py-1.5 text-xs text-white shadow-lg backdrop-blur-sm">
                <span>2s</span>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={1}
                  value={sliderValue}
                  onChange={handleSliderChange}
                  aria-label="Slideshow duration"
                  className="h-1.5 w-32 cursor-pointer appearance-none rounded-lg accent-indigo-500"
                  style={{
                    background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${(sliderValue / 2) * 100}%, rgba(255,255,255,0.2) ${(sliderValue / 2) * 100}%, rgba(255,255,255,0.2) 100%)`,
                  }}
                />
                <span>10s</span>
              </div>
            </div>
          )}
        </div>
      )}

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