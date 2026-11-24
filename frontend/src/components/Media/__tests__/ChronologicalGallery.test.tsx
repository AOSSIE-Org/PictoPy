import { createRef } from 'react';
import { act, render, waitFor } from '@/test-utils';
import { setGallerySize, type GallerySize } from '@/features/galleryViewSlice';
import type { Image } from '@/types/Media';
import {
  ChronologicalGallery,
  type MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import { ChronologicalFavoritesGallery } from '@/components/Media/ChronologicalFavoritesGallery';

jest.mock('@/components/Media/ImageCard', () => ({ ImageCard: () => null }));
jest.mock('@/components/Media/VideoCard', () => ({ VideoCard: () => null }));
jest.mock('@/components/Media/MediaView', () => ({ MediaView: () => null }));
jest.mock('@/components/VideoPlayer/VideoPlayerOverlay', () => ({
  VideoPlayerOverlay: () => null,
}));
jest.mock('@/components/GalleryViewSelector', () => ({
  GalleryViewSelector: () => null,
}));

const makeImage = (id: string, date: string): Image => ({
  id,
  path: `/images/${id}.jpg`,
  thumbnailPath: `/thumbnails/${id}.jpg`,
  folder_id: 'folder-1',
  isTagged: false,
  metadata: {
    name: `${id}.jpg`,
    date_created: date,
    width: 100,
    height: 100,
    file_location: `/images/${id}.jpg`,
    file_size: 100,
    item_type: 'image',
  },
});

const images = [
  makeImage('february', '2024-02-10'),
  makeImage('january', '2024-01-10'),
];

const offsetsBySize: Record<GallerySize, Record<string, number>> = {
  small: { '2024-02': 100, '2024-01': 200 },
  medium: { '2024-02': 120, '2024-01': 240 },
  large: { '2024-02': 140, '2024-01': 280 },
};

const expectedMarkers = (size: GallerySize): MonthMarker[] => [
  { offset: offsetsBySize[size]['2024-02'], month: 'February', year: '2024' },
  { offset: offsetsBySize[size]['2024-01'], month: 'January', year: '2024' },
];

afterEach(() => {
  jest.restoreAllMocks();
});

describe.each([
  [
    'ChronologicalGallery',
    (
      scrollContainerRef: React.RefObject<HTMLDivElement | null>,
      onMonthOffsetsChange: (markers: MonthMarker[]) => void,
    ) => (
      <ChronologicalGallery
        images={images}
        onMonthOffsetsChange={onMonthOffsetsChange}
        scrollContainerRef={scrollContainerRef}
      />
    ),
  ],
  [
    'ChronologicalFavoritesGallery',
    (
      scrollContainerRef: React.RefObject<HTMLDivElement | null>,
      onMonthOffsetsChange: (markers: MonthMarker[]) => void,
    ) => (
      <ChronologicalFavoritesGallery
        images={images}
        videos={[]}
        onMonthOffsetsChange={onMonthOffsetsChange}
        scrollContainerRef={scrollContainerRef}
      />
    ),
  ],
])('%s', (_name, renderGallery) => {
  it('recalculates month offsets through size changes in both directions', async () => {
    jest
      .spyOn(HTMLElement.prototype, 'getBoundingClientRect')
      .mockImplementation(function (this: HTMLElement) {
        const month = this.dataset.timelineMonth;
        const size = this.querySelector<HTMLElement>('[data-gallery-size]')
          ?.dataset.gallerySize as GallerySize | undefined;
        const top = month && size ? offsetsBySize[size][month] : 0;

        return {
          x: 0,
          y: top,
          top,
          left: 0,
          bottom: top,
          right: 0,
          width: 0,
          height: 0,
          toJSON: () => ({}),
        };
      });

    const scrollContainerRef = createRef<HTMLDivElement>();
    const onMonthOffsetsChange = jest.fn();
    const { store } = render(
      <div ref={scrollContainerRef}>
        {renderGallery(scrollContainerRef, onMonthOffsetsChange)}
      </div>,
      { preloadedState: { galleryView: { size: 'small' } } },
    );

    await waitFor(() =>
      expect(onMonthOffsetsChange).toHaveBeenLastCalledWith(
        expectedMarkers('small'),
      ),
    );

    for (const size of ['medium', 'large', 'medium', 'small'] as const) {
      act(() => store.dispatch(setGallerySize(size)));
      await waitFor(() =>
        expect(onMonthOffsetsChange).toHaveBeenLastCalledWith(
          expectedMarkers(size),
        ),
      );
    }
  });
});
