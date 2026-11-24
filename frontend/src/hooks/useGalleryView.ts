import { useCallback } from 'react';
import {
  GALLERY_VIEW_STORAGE_KEY,
  setGallerySize,
  type GallerySize,
} from '@/features/galleryViewSlice';
import { useAppDispatch, useAppSelector } from '@/store/hooks';

export function useGalleryView(): [GallerySize, (size: GallerySize) => void] {
  const dispatch = useAppDispatch();
  const size = useAppSelector((state) => state.galleryView.size);

  const updateSize = useCallback(
    (nextSize: GallerySize) => {
      try {
        localStorage.setItem(
          GALLERY_VIEW_STORAGE_KEY,
          JSON.stringify({ size: nextSize }),
        );
      } catch {
        // Keep the preference usable for this session when storage is unavailable.
      }
      dispatch(setGallerySize(nextSize));
    },
    [dispatch],
  );

  return [size, updateSize];
}

export const GALLERY_GRID_SIZES: Record<
  GallerySize,
  { minWidth: number; gap: number }
> = {
  small: { minWidth: 160, gap: 8 },
  medium: { minWidth: 224, gap: 16 },
  large: { minWidth: 288, gap: 24 },
};
