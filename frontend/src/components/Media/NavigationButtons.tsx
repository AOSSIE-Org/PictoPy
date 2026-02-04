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
        className="group absolute inset-y-0 left-0 z-30 flex w-20 cursor-pointer items-center justify-center bg-transparent text-white"
        aria-label="Previous image"
      >
        <span className="flex items-center justify-center rounded-full p-3 backdrop-blur-md transition-all duration-200 group-hover:bg-black/80 group-hover:shadow-lg">
          <ChevronLeft className="h-6 w-6" />
        </span>
      </button>

      <button
        onClick={onNext}
        className="group absolute inset-y-0 right-0 z-30 flex w-20 cursor-pointer items-center justify-center bg-transparent text-white"
        aria-label="Next image"
      >
        <span className="flex items-center justify-center rounded-full p-3 backdrop-blur-md transition-all duration-200 group-hover:bg-black/80 group-hover:shadow-lg">
          <ChevronRight className="h-6 w-6" />
        </span>
      </button>
    </>
  );
};
