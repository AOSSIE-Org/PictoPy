import type { SyntheticEvent } from 'react';

export const PLACEHOLDER_IMAGE_SRC = '/placeholder.svg';

/**
 * Builds an `<img>` onError handler that swaps in a fallback image exactly once
 * and detaches itself, so a broken fallback cannot trigger an error loop.
 *
 * Centralizes the handler that was previously copy-pasted across the media and
 * memories components (each with its own fallback asset).
 */
export const createImageErrorHandler =
  (fallbackSrc: string = PLACEHOLDER_IMAGE_SRC) =>
  (event: SyntheticEvent<HTMLImageElement>) => {
    const img = event.currentTarget;
    img.onerror = null;
    img.src = fallbackSrc;
  };

/** Shared, stable handler for components that fall back to the placeholder. */
export const handlePlaceholderImageError = createImageErrorHandler();
