import React from 'react';
import { ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

interface ZoomControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRotate: () => void;
  onReset: () => void;
  showThumbnails: boolean;
}

export const ZoomControls: React.FC<ZoomControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onRotate,
  onReset,
  showThumbnails,
}) => {
  return (
    <div
      className={`absolute ${
        showThumbnails ? 'bottom-32' : 'bottom-12'
      } left-1/2 z-10 flex -translate-x-1/2 transform flex-col gap-4 rounded-xl bg-white/70 p-3 shadow-lg backdrop-blur-md transition-all duration-300 dark:bg-black/50 dark:shadow-none`}
    >
      <div className="flex gap-2">
        <button
          onClick={onZoomOut}
          className="cursor-pointer rounded-md bg-black/5 p-2 text-gray-700 transition-all duration-200 hover:bg-black/10 hover:text-black hover:shadow-md dark:bg-white/10 dark:text-white dark:hover:bg-white/20 dark:hover:text-white"
          aria-label="Zoom Out"
          title="Zoom Out"
        >
          <ZoomOut className="h-5 w-5" />
        </button>

        <button
          onClick={onReset}
          className="cursor-pointer rounded-md bg-black/5 px-3 py-2 text-sm font-medium text-gray-700 transition-all duration-200 hover:bg-black/10 hover:text-black hover:shadow-md dark:bg-white/10 dark:text-white dark:hover:bg-white/20 dark:hover:text-white"
          aria-label="Reset"
        >
          Reset
        </button>

        <button
          onClick={onZoomIn}
          className="cursor-pointer rounded-md bg-black/5 p-2 text-gray-700 transition-all duration-200 hover:bg-black/10 hover:text-black hover:shadow-md dark:bg-white/10 dark:text-white dark:hover:bg-white/20 dark:hover:text-white"
          aria-label="Zoom In"
          title="Zoom In"
        >
          <ZoomIn className="h-5 w-5" />
        </button>

        <button
          onClick={onRotate}
          className="cursor-pointer rounded-md bg-black/5 p-2 text-gray-700 transition-all duration-200 hover:bg-black/10 hover:text-black hover:shadow-md dark:bg-white/10 dark:text-white dark:hover:bg-white/20 dark:hover:text-white"
          aria-label="Rotate"
          title="Rotate"
        >
          <RotateCw className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};
