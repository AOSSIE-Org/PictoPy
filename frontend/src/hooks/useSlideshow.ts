import { useState, useEffect, useCallback } from 'react';

export const useSlideshow = (totalImages: number, onNextImage: () => void) => {
  const [isSlideshowActive, setIsSlideshowActive] = useState(false);

  useEffect(() => {
    let slideshowInterval: NodeJS.Timeout | null = null;

    if (isSlideshowActive && totalImages > 1) {
      slideshowInterval = setInterval(() => {
        onNextImage();
      }, 3000);
    }

    return () => {
      if (slideshowInterval) {
        clearInterval(slideshowInterval);
      }
    };
  }, [isSlideshowActive, totalImages, onNextImage]);

  const toggleSlideshow = useCallback(() => {
    setIsSlideshowActive((prev) => !prev);
  }, []);

  return {
    isSlideshowActive,
    toggleSlideshow,
  };
};
