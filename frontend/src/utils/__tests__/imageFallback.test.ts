import type { SyntheticEvent } from 'react';
import {
  createImageErrorHandler,
  handlePlaceholderImageError,
  PLACEHOLDER_IMAGE_SRC,
} from '../imageFallback';

describe('imageFallback', () => {
  describe('PLACEHOLDER_IMAGE_SRC', () => {
    test('exports the default placeholder path', () => {
      expect(PLACEHOLDER_IMAGE_SRC).toBe('/placeholder.svg');
    });
  });

  describe('createImageErrorHandler', () => {
    test('swaps image source to default placeholder and clears onerror', () => {
      const handler = createImageErrorHandler();
      const mockImg = {
        src: 'broken-image.jpg',
        onerror: jest.fn(),
      } as unknown as HTMLImageElement;

      const event = {
        currentTarget: mockImg,
      } as SyntheticEvent<HTMLImageElement>;

      handler(event);

      expect(mockImg.src).toBe(PLACEHOLDER_IMAGE_SRC);
      expect(mockImg.onerror).toBeNull();
    });

    test('swaps image source to custom fallback when provided', () => {
      const customFallback = '/custom/fallback-avatar.png';
      const handler = createImageErrorHandler(customFallback);
      const mockImg = {
        src: 'missing-avatar.jpg',
        onerror: jest.fn(),
      } as unknown as HTMLImageElement;

      const event = {
        currentTarget: mockImg,
      } as SyntheticEvent<HTMLImageElement>;

      handler(event);

      expect(mockImg.src).toBe(customFallback);
      expect(mockImg.onerror).toBeNull();
    });

    test('detaches onerror to prevent infinite loop on broken fallback', () => {
      const handler = createImageErrorHandler('/missing-fallback.svg');
      const initialErrorHandler = jest.fn();
      const mockImg = {
        src: 'initial-broken.jpg',
        onerror: initialErrorHandler,
      } as unknown as HTMLImageElement;

      const event = {
        currentTarget: mockImg,
      } as SyntheticEvent<HTMLImageElement>;

      handler(event);

      expect(mockImg.onerror).toBeNull();
    });
  });

  describe('handlePlaceholderImageError', () => {
    test('is a stable handler instance that uses the default placeholder', () => {
      const mockImg = {
        src: 'failed-thumbnail.jpg',
        onerror: jest.fn(),
      } as unknown as HTMLImageElement;

      const event = {
        currentTarget: mockImg,
      } as SyntheticEvent<HTMLImageElement>;

      handlePlaceholderImageError(event);

      expect(mockImg.src).toBe(PLACEHOLDER_IMAGE_SRC);
      expect(mockImg.onerror).toBeNull();
    });
  });
});
