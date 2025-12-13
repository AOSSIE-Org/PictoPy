import {
  selectImages,
  selectCurrentViewIndex,
  selectImageSource,
  selectIsImageViewOpen,
  selectNeedsGalleryRefresh,
} from '../imageSelectors';
import { RootState } from '@/app/store';
import { ImageSource } from '../imageSlice';

// Helper to create mock state
const createMockState = (imageState: {
  images?: any[];
  currentViewIndex?: number;
  source?: ImageSource;
}): RootState =>
  ({
    images: {
      images: imageState.images || [],
      currentViewIndex: imageState.currentViewIndex ?? -1,
      source: imageState.source ?? null,
    },
  }) as RootState;

describe('imageSelectors', () => {
  describe('selectImages', () => {
    it('should return images array', () => {
      const mockImages = [{ id: '1' }, { id: '2' }];
      const state = createMockState({ images: mockImages });

      expect(selectImages(state)).toEqual(mockImages);
    });
  });

  describe('selectCurrentViewIndex', () => {
    it('should return current view index', () => {
      const state = createMockState({ currentViewIndex: 5 });

      expect(selectCurrentViewIndex(state)).toBe(5);
    });
  });

  describe('selectImageSource', () => {
    it('should return image source', () => {
      const state = createMockState({ source: 'cluster' });

      expect(selectImageSource(state)).toBe('cluster');
    });

    it('should return null when no source set', () => {
      const state = createMockState({});

      expect(selectImageSource(state)).toBeNull();
    });
  });

  describe('selectIsImageViewOpen', () => {
    it('should return true when index >= 0', () => {
      const state = createMockState({ currentViewIndex: 0 });

      expect(selectIsImageViewOpen(state)).toBe(true);
    });

    it('should return false when index is -1', () => {
      const state = createMockState({ currentViewIndex: -1 });

      expect(selectIsImageViewOpen(state)).toBe(false);
    });
  });

  describe('selectNeedsGalleryRefresh', () => {
    it('should return false when source is gallery', () => {
      const state = createMockState({ source: 'gallery' });

      expect(selectNeedsGalleryRefresh(state)).toBe(false);
    });

    it('should return false when source is null', () => {
      const state = createMockState({ source: null });

      expect(selectNeedsGalleryRefresh(state)).toBe(false);
    });

    it('should return true when source is cluster', () => {
      const state = createMockState({ source: 'cluster' });

      expect(selectNeedsGalleryRefresh(state)).toBe(true);
    });

    it('should return true when source is search', () => {
      const state = createMockState({ source: 'search' });

      expect(selectNeedsGalleryRefresh(state)).toBe(true);
    });

    it('should return true when source is album', () => {
      const state = createMockState({ source: 'album' });

      expect(selectNeedsGalleryRefresh(state)).toBe(true);
    });
  });

  describe('Issue #706: Navigation state detection', () => {
    it('should detect need for refresh after cluster view', () => {
      // User was viewing a person's cluster
      const stateAfterCluster = createMockState({ source: 'cluster' });

      // Home page should detect this and refetch
      expect(selectNeedsGalleryRefresh(stateAfterCluster)).toBe(true);
    });

    it('should not need refresh when already on gallery', () => {
      // User is on Home with gallery data
      const stateOnGallery = createMockState({ source: 'gallery' });

      // No need to refetch
      expect(selectNeedsGalleryRefresh(stateOnGallery)).toBe(false);
    });
  });
});
