import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface NavigationButtonsProps {
  onPrevious: () => void;
  onNext: () => void;
  previousLabel?: string;
  nextLabel?: string;
}

export const NavigationButtons: React.FC<NavigationButtonsProps> = ({
  onPrevious,
  onNext,
  previousLabel = 'Previous image',
  nextLabel = 'Next image',
}) => {
  return (
    <>
      <button
        onClick={onPrevious}
        className="group absolute inset-y-0 left-0 z-30 flex w-20 cursor-pointer items-center justify-center bg-transparent text-gray-800 dark:text-white"
        aria-label={previousLabel}
      >
        <span className="flex items-center justify-center rounded-full bg-white/80 p-3 shadow-md backdrop-blur-md transition-all duration-200 group-hover:bg-white group-hover:shadow-lg dark:bg-transparent dark:shadow-none dark:group-hover:bg-black/80 dark:group-hover:shadow-lg">
          <ChevronLeft className="h-6 w-6" />
        </span>
      </button>

      <button
        onClick={onNext}
        className="group absolute inset-y-0 right-0 z-30 flex w-20 cursor-pointer items-center justify-center bg-transparent text-gray-800 dark:text-white"
        aria-label={nextLabel}
      >
        <span className="flex items-center justify-center rounded-full bg-white/80 p-3 shadow-md backdrop-blur-md transition-all duration-200 group-hover:bg-white group-hover:shadow-lg dark:bg-transparent dark:shadow-none dark:group-hover:bg-black/80 dark:group-hover:shadow-lg">
          <ChevronRight className="h-6 w-6" />
        </span>
      </button>
    </>
  );
};
