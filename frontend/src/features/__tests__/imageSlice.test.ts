import imageReducer, {
  setImages,
  setGalleryImages,
  setClusterImages,
  setSearchImages,
  setCurrentViewIndex,
  closeImageView,
  clearImages,
  ImageSource,
} from '../imageSlice';
import { Image } from '@/types/Media';

describe('imageSlice', () => {
  const mockImages: Image[] = [
    { id: '1', path: '/photo1.jpg' } as Image,
    { id: '2', path: '/photo2.jpg' } as Image,
  ];

  const initialState = {
    images: [],
    currentViewIndex: -1,
    source: null as ImageSource,
  };

  describe('setGalleryImages', () => {
    it('should set images with gallery source', () => {
      const state = imageReducer(initialState, setGalleryImages(mockImages));

      expect(state.images).toEqual(mockImages);
      expect(state.source).toBe('gallery');
    });
  });

  describe('setClusterImages', () => {
    it('should set images with cluster source', () => {
      const state = imageReducer(initialState, setClusterImages(mockImages));

      expect(state.images).toEqual(mockImages);
      expect(state.source).toBe('cluster');
    });
  });

  describe('setSearchImages', () => {
    it('should set images with search source', () => {
      const state = imageReducer(initialState, setSearchImages(mockImages));

      expect(state.images).toEqual(mockImages);
      expect(state.source).toBe('search');
    });
  });

  describe('setImages (legacy)', () => {
    it('should set images without changing source', () => {
      const stateWithSource = {
        ...initialState,
        source: 'gallery' as ImageSource,
      };
      const state = imageReducer(stateWithSource, setImages(mockImages));

      expect(state.images).toEqual(mockImages);
      expect(state.source).toBe('gallery'); // Source unchanged
    });
  });

  describe('clearImages', () => {
    it('should reset images and source to initial state', () => {
      const populatedState = {
        images: mockImages,
        currentViewIndex: 1,
        source: 'cluster' as ImageSource,
      };

      const state = imageReducer(populatedState, clearImages());

      expect(state.images).toEqual([]);
      expect(state.currentViewIndex).toBe(-1);
      expect(state.source).toBeNull();
    });
  });

  describe('setCurrentViewIndex', () => {
    it('should set valid index', () => {
      const stateWithImages = { ...initialState, images: mockImages };
      const state = imageReducer(stateWithImages, setCurrentViewIndex(1));

      expect(state.currentViewIndex).toBe(1);
    });

    it('should allow -1 to close view', () => {
      const stateWithImages = {
        ...initialState,
        images: mockImages,
        currentViewIndex: 1,
      };
      const state = imageReducer(stateWithImages, setCurrentViewIndex(-1));

      expect(state.currentViewIndex).toBe(-1);
    });
  });

  describe('closeImageView', () => {
    it('should set currentViewIndex to -1', () => {
      const stateWithOpenView = { ...initialState, currentViewIndex: 2 };
      const state = imageReducer(stateWithOpenView, closeImageView());

      expect(state.currentViewIndex).toBe(-1);
    });
  });

  describe('Issue #706: State isolation', () => {
    it('should track source when switching from gallery to cluster', () => {
      // Simulate: Home loads gallery
      let state = imageReducer(
        initialState,
        setGalleryImages([...mockImages, { id: '3', path: '/photo3.jpg' } as Image]),
      );
      expect(state.images).toHaveLength(3);
      expect(state.source).toBe('gallery');

      // Simulate: Navigate to person view (cluster)
      state = imageReducer(state, setClusterImages(mockImages));
      expect(state.images).toHaveLength(2);
      expect(state.source).toBe('cluster');

      // Source is now 'cluster', Home page can detect this and refetch
      expect(state.source).not.toBe('gallery');
    });

    it('should allow Home to detect stale cluster data', () => {
      // After viewing cluster, source is 'cluster'
      const stateAfterCluster = {
        images: mockImages,
        currentViewIndex: -1,
        source: 'cluster' as ImageSource,
      };

      // Home page checks: needsRefresh = source !== 'gallery'
      const needsRefresh = stateAfterCluster.source !== 'gallery';
      expect(needsRefresh).toBe(true);
    });
  });
});
