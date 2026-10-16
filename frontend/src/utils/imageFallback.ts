import type { SyntheticEvent } from 'react';

export const PLACEHOLDER_IMAGE_SRC = '/placeholder.svg';

// The fallback has to be a local asset that cannot fail in turn: clearing
// img.onerror does not detach the React onError prop callers attach this with.
export const createImageErrorHandler =
  (fallbackSrc: string = PLACEHOLDER_IMAGE_SRC) =>
  (event: SyntheticEvent<HTMLImageElement>) => {
    const img = event.currentTarget;
    img.onerror = null;
    img.src = fallbackSrc;
  };

/** Shared, stable handler for components that fall back to the placeholder. */
export const handlePlaceholderImageError = createImageErrorHandler();
