import type { SyntheticEvent } from 'react';

export const PLACEHOLDER_IMAGE_SRC = '/placeholder.svg';

// Detaches itself after the first swap, so a broken fallback cannot loop.
export const createImageErrorHandler =
  (fallbackSrc: string = PLACEHOLDER_IMAGE_SRC) =>
  (event: SyntheticEvent<HTMLImageElement>) => {
    const img = event.currentTarget;
    img.onerror = null;
    img.src = fallbackSrc;
  };

/** Shared, stable handler for components that fall back to the placeholder. */
export const handlePlaceholderImageError = createImageErrorHandler();
