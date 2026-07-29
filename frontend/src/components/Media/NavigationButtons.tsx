import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface NavigationButtonsProps {
  onPrevious: () => void;
  onNext: () => void;
  previousLabel?: string;
  nextLabel?: string;
  disablePrevious?: boolean;
  disableNext?: boolean;
}

// Scrim chip so the arrow stays visible over any image. In dark mode we keep a
// persistent black/50 background to match the other viewer controls, otherwise a
// white chevron disappears on a fully white image. See PictoPy#1422.
const chipBase =
  'flex items-center justify-center rounded-full bg-white/80 p-3 shadow-md backdrop-blur-md transition-all duration-200 dark:bg-black/50 dark:shadow-none';
// Hover only on enabled arrows. Darken the dark scrim on hover rather than
// lightening it, so the chevron never loses contrast over a bright image.
const chipHover =
  'group-hover:bg-white group-hover:shadow-lg dark:group-hover:bg-black/70 dark:group-hover:shadow-lg';

export const NavigationButtons: React.FC<NavigationButtonsProps> = ({
  onPrevious,
  onNext,
  previousLabel = 'Previous image',
  nextLabel = 'Next image',
  disablePrevious = false,
  disableNext = false,
}) => {
  // Full class strings so Tailwind's scanner keeps left-0/right-0 (no dynamic concat).
  const buttonClasses = (disabled: boolean, position: string) =>
    `absolute inset-y-0 ${position} z-30 flex w-20 items-center justify-center bg-transparent text-gray-800 dark:text-white ${
      disabled ? 'cursor-not-allowed opacity-40' : 'group cursor-pointer'
    }`;

  const chipClasses = (disabled: boolean) =>
    disabled ? chipBase : `${chipBase} ${chipHover}`;

  return (
    <>
      <button
        onClick={onPrevious}
        disabled={disablePrevious}
        className={buttonClasses(disablePrevious, 'left-0')}
        aria-label={previousLabel}
      >
        <span className={chipClasses(disablePrevious)}>
          <ChevronLeft className="h-6 w-6" />
        </span>
      </button>

      <button
        onClick={onNext}
        disabled={disableNext}
        className={buttonClasses(disableNext, 'right-0')}
        aria-label={nextLabel}
      >
        <span className={chipClasses(disableNext)}>
          <ChevronRight className="h-6 w-6" />
        </span>
      </button>
    </>
  );
};
