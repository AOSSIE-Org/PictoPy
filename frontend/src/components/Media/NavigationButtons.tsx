import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface NavigationButtonsProps {
  onPrevious: () => void;
  onNext: () => void;
}

export const NavigationButtons: React.FC<NavigationButtonsProps> = ({
  onPrevious,
  onNext,
}) => {
  return (
    <>
      {/* Left Hotspot */}
      <button
        className="
          group absolute left-0 top-0 z-20 h-full w-20 cursor-pointer bg-transparent
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50 focus-visible:ring-inset
        "
        onClick={onPrevious}
        aria-label="Previous image"
        type="button"
      >
        <div
          className="
            absolute top-1/2 left-4 z-30 flex -translate-y-1/2 transform
            items-center rounded-full bg-black/30 p-3 text-white
            backdrop-blur-md transition-all duration-200
            group-hover:bg-white/40 group-hover:shadow-lg
            group-focus-visible:bg-white/40 group-focus-visible:shadow-lg
          "
        >
          <ChevronLeft className="h-6 w-6" />
        </div>
      </button>

      {/* Right Hotspot */}
      <button
        className="
          group absolute right-0 top-0 z-20 h-full w-20 cursor-pointer bg-transparent
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50 focus-visible:ring-inset
        "
        onClick={onNext}
        aria-label="Next image"
        type="button"
      >
        <div
          className="
            absolute top-1/2 right-4 z-30 flex -translate-y-1/2 transform
            items-center rounded-full bg-black/30 p-3 text-white
            backdrop-blur-md transition-all duration-200
            group-hover:bg-white/40 group-hover:shadow-lg
            group-focus-visible:bg-white/40 group-focus-visible:shadow-lg
          "
        >
          <ChevronRight className="h-6 w-6" />
        </div>
      </button>
    </>
  );
};
