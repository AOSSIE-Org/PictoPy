import { useState, useEffect, useCallback } from 'react';

export const useSlideshow = (
  totalImages: number,
  onNextImage: () => void,
  onLoopToStart?: () => void,
  currentIndex?: number,
) => {
  const [isSlideshowActive, setIsSlideshowActive] = useState(false);
  const [duration, setDuration] = useState(3000); // default 3s, now changeable

  useEffect(() => {
    let slideshowInterval: NodeJS.Timeout | null = null;
    if (isSlideshowActive && totalImages > 1) {
      slideshowInterval = setInterval(() => {
        if (
          currentIndex !== undefined &&
          onLoopToStart &&
          currentIndex >= totalImages - 1
        ) {
          onLoopToStart();
        } else {
          onNextImage();
        }
      }, duration); // <-- was 3000, now uses the duration state
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
    duration, // <-- added, so timer restarts if duration changes
  ]);

  const toggleSlideshow = useCallback(() => {
    setIsSlideshowActive((prev) => !prev);
  }, []);

  return {
    isSlideshowActive,
    toggleSlideshow,
    duration,        // <-- exposing current duration
    setDuration,      // <-- exposing the setter so other files can change it
  };
};