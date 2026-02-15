import { useState, useEffect, useCallback } from 'react';

export const useSlideshow = (
  totalImages: number,
  onNextImage: () => void,
  onLoopToStart?: () => void,
  currentIndex?: number,
) => {
  const [isSlideshowActive, setIsSlideshowActive] = useState(false);

  useEffect(() => {
    let slideshowInterval: NodeJS.Timeout | null = null;

    if (isSlideshowActive && totalImages > 1) {
      slideshowInterval = setInterval(() => {
        // Loop back to first image when at the end
        if (
          currentIndex !== undefined &&
          onLoopToStart &&
          currentIndex >= totalImages - 1
        ) {
          onLoopToStart();
        } else {
          onNextImage();
        }
      }, 3000);
    }

    return () => {
      if (slideshowInterval) {
        clearInterval(slideshowInterval);
      }
    };
  }, [
    isSlideshowActive,
    totalImages,
    onNextImage,
    onLoopToStart,
    currentIndex,
  ]);

  const toggleSlideshow = useCallback(() => {
    setIsSlideshowActive((prev) => !prev);
  }, []);

  return {
    isSlideshowActive,
    toggleSlideshow,
  };
};
