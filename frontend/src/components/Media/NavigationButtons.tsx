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
      <div
        className="group absolute left-0 top-0 z-20 h-full w-20 cursor-pointer"
        onClick={onPrevious}
      >
        <button
          className="absolute top-1/2 left-4 z-30 flex -translate-y-1/2 transform 
                     items-center rounded-full bg-black/30 p-3 text-white 
                     backdrop-blur-md transition-all duration-200 
                     group-hover:bg-white/40 group-hover:shadow-lg"
          aria-label="Previous image"
        >
          <ChevronLeft className="h-6 w-6" />
        </button>
      </div>

      {/* Right Hotspot */}
      <div
        className="group absolute right-0 top-0 z-20 h-full w-20 cursor-pointer"
        onClick={onNext}
      >
        <button
          className="absolute top-1/2 right-4 z-30 flex -translate-y-1/2 transform 
                     items-center rounded-full bg-black/30 p-3 text-white 
                     backdrop-blur-md transition-all duration-200 
                     group-hover:bg-white/40 group-hover:shadow-lg"
          aria-label="Next image"
        >
          <ChevronRight className="h-6 w-6" />
        </button>
      </div>
    </>
  );
};
