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
      {/* Previous */}
      <button
        onClick={onPrevious}
        aria-label="Previous image"
        className="group absolute top-1/2 left-0 z-30 flex h-40 w-40 -translate-y-1/2 items-center justify-center bg-transparent"
      >
        <div className="pointer-events-none rounded-full bg-black/30 p-3 text-white backdrop-blur-md transition-all duration-200 group-hover:scale-110 group-hover:bg-black/50 group-hover:shadow-lg">
          <ChevronLeft className="h-6 w-6" />
        </div>
      </button>

      {/* Next */}
      <button
        onClick={onNext}
        aria-label="Next image"
        className="group absolute top-1/2 right-0 z-30 flex h-40 w-40 -translate-y-1/2 items-center justify-center bg-transparent"
      >
        <div className="pointer-events-none rounded-full bg-black/30 p-3 text-white backdrop-blur-md transition-all duration-200 group-hover:scale-110 group-hover:bg-black/50 group-hover:shadow-lg">
          <ChevronRight className="h-6 w-6" />
        </div>
      </button>
    </>
  );
};
