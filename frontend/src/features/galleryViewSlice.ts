import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export type GallerySize = 'small' | 'medium' | 'large';

export interface GalleryViewState {
  size: GallerySize;
}

export const GALLERY_VIEW_STORAGE_KEY = 'pictopy-gallery-view';
const LEGACY_DENSITY_KEY = 'pictopy-gallery-density';

function isGallerySize(value: unknown): value is GallerySize {
  return value === 'small' || value === 'medium' || value === 'large';
}

function getInitialState(): GalleryViewState {
  try {
    const stored = localStorage.getItem(GALLERY_VIEW_STORAGE_KEY);
    if (stored) {
      const parsed: unknown = JSON.parse(stored);
      if (typeof parsed === 'object' && parsed !== null && 'size' in parsed) {
        return { size: isGallerySize(parsed.size) ? parsed.size : 'medium' };
      }
    }

    const previousDensity = localStorage.getItem(LEGACY_DENSITY_KEY);
    if (previousDensity === 'compact') return { size: 'small' };
    if (previousDensity === 'spacious') return { size: 'large' };
  } catch {
    return { size: 'medium' };
  }

  return { size: 'medium' };
}

const galleryViewSlice = createSlice({
  name: 'galleryView',
  initialState: getInitialState,
  reducers: {
    setGallerySize(state, action: PayloadAction<GallerySize>) {
      state.size = action.payload;
    },
  },
});

export const { setGallerySize } = galleryViewSlice.actions;
export default galleryViewSlice.reducer;
