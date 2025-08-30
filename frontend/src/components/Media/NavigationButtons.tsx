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
      <button
        onClick={onPrevious}
        className="absolute top-1/2 left-4 z-30 flex -translate-y-1/2 transform items-center rounded-full bg-black/30 p-3 text-white backdrop-blur-md transition-all duration-200 hover:bg-black/50 hover:shadow-lg"
        aria-label="Previous image"
      >
        <ChevronLeft className="h-6 w-6" />
      </button>

      <button
        onClick={onNext}
        className="absolute top-1/2 right-4 z-30 flex -translate-y-1/2 transform items-center rounded-full bg-black/30 p-3 text-white backdrop-blur-md transition-all duration-200 hover:bg-black/50 hover:shadow-lg"
        aria-label="Next image"
      >
        <ChevronRight className="h-6 w-6" />
      </button>
    </>
  );
};
