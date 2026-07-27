import type { MemoryCard, MemoryImage } from '@/api/api-functions/memories';
import {
  MEMORY_PLACEHOLDER_IMAGE,
  formatDateRange,
  formatEventType,
  formatMemoryDate,
  formatMemorySubtitle,
  formatPhotoCount,
  getCoverUrl,
  getMemoryImageUrl,
  getThumbnailUrl,
} from '../memories';

// The shared setup mock only provides `invoke`; these helpers need
// convertFileSrc, so override the module locally as the other suites do.
// Babel hoists this above the imports.
jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
  convertFileSrc: jest.fn((path: string) => `asset://localhost/${path}`),
}));

const makeMemory = (overrides: Partial<MemoryCard> = {}): MemoryCard => ({
  memory_id: 'mem-1',
  dedupe_key: 'anniv:07-26:2024',
  event_type: 'anniversary',
  status: 'complete',
  title: '2 years ago today',
  subtitle: null,
  place_label: null,
  center_lat: null,
  center_lon: null,
  surface_date: '2026-07-26',
  period_start: null,
  period_end: null,
  image_count: 3,
  cover_image_id: 'img-0',
  cover_thumbnail_path: '/thumbs/0.jpg',
  score: 0.7,
  notified_at: null,
  viewed_at: null,
  dismissed: false,
  created_at: null,
  ...overrides,
});

const makeImage = (overrides: Partial<MemoryImage> = {}): MemoryImage => ({
  id: 'img-0',
  path: '/photos/0.jpg',
  thumbnailPath: '/thumbs/0.jpg',
  captured_at: '2024-07-26 10:00:00',
  latitude: null,
  longitude: null,
  isFavourite: false,
  sort_order: 0,
  score: 1,
  ...overrides,
});

describe('formatMemoryDate', () => {
  it('formats an ISO date', () => {
    expect(formatMemoryDate('2024-07-26T10:00:00')).toContain('2024');
  });

  it.each([null, '', 'not-a-date'])('returns empty for %p', (value) => {
    expect(formatMemoryDate(value as string | null)).toBe('');
  });
});

describe('formatDateRange', () => {
  it('collapses a single day to one date', () => {
    const single = formatDateRange(
      '2024-07-26T09:00:00',
      '2024-07-26T18:00:00',
    );
    expect(single).toBe(formatMemoryDate('2024-07-26T09:00:00'));
  });

  it('collapses a range within one month', () => {
    expect(formatDateRange('2024-07-26T09:00:00', '2024-07-28T09:00:00')).toBe(
      '26–28 July 2024',
    );
  });

  it('spans months with both endpoints', () => {
    const range = formatDateRange('2024-07-30T09:00:00', '2024-08-02T09:00:00');
    expect(range).toContain('–');
    expect(range).toContain('2024');
  });

  it('falls back to the start date when the end is missing', () => {
    expect(formatDateRange('2024-07-26T09:00:00', null)).toBe(
      formatMemoryDate('2024-07-26T09:00:00'),
    );
  });

  it.each([null, 'nonsense'])('returns empty for start %p', (value) => {
    expect(formatDateRange(value as string | null, '2024-07-26')).toBe('');
  });
});

describe('formatPhotoCount', () => {
  it.each([
    [0, '0 photos'],
    [1, '1 photo'],
    [2, '2 photos'],
  ])('formats %p as %p', (count, expected) => {
    expect(formatPhotoCount(count)).toBe(expected);
  });
});

describe('formatEventType', () => {
  it.each([
    ['anniversary', 'On this day'],
    ['import_event', 'Event'],
    ['semantic_event', 'Highlight'],
  ] as const)('labels %p as %p', (eventType, expected) => {
    expect(formatEventType(eventType)).toBe(expected);
  });
});

describe('formatMemorySubtitle', () => {
  it('prefers the curator-provided subtitle', () => {
    expect(formatMemorySubtitle(makeMemory({ subtitle: 'July 2024' }))).toBe(
      'July 2024',
    );
  });

  it('falls back to the date span', () => {
    const memory = makeMemory({
      subtitle: null,
      period_start: '2024-07-26T09:00:00',
      period_end: '2024-07-28T09:00:00',
    });
    expect(formatMemorySubtitle(memory)).toBe('26–28 July 2024');
  });

  it('falls back to the surface date when there is no span', () => {
    expect(formatMemorySubtitle(makeMemory())).toBe(
      formatMemoryDate('2026-07-26'),
    );
  });
});

describe('image URLs', () => {
  it.each([null, undefined, ''])('returns the placeholder for %p', (value) => {
    expect(getMemoryImageUrl(value as string | null)).toBe(
      MEMORY_PLACEHOLDER_IMAGE,
    );
  });

  it('converts a real path through the Tauri asset protocol', () => {
    expect(getMemoryImageUrl('/photos/0.jpg')).toBe(
      'asset://localhost//photos/0.jpg',
    );
  });

  it('prefers the thumbnail but falls back to the full-size path', () => {
    expect(getThumbnailUrl(makeImage())).toContain('/thumbs/0.jpg');
    expect(getThumbnailUrl(makeImage({ thumbnailPath: null }))).toContain(
      '/photos/0.jpg',
    );
  });

  it('returns the placeholder when a memory has no cover', () => {
    expect(getCoverUrl(makeMemory({ cover_thumbnail_path: null }))).toBe(
      MEMORY_PLACEHOLDER_IMAGE,
    );
  });
});
