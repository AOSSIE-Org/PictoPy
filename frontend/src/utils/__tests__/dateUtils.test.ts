import { getTimeAgo, groupImagesByYearMonthFromMetadata } from '../dateUtils';
import { Image, ImageMetadata } from '@/types/Media';

/* ------------------------------------------------------------------ */
/*  getTimeAgo                                                        */
/* ------------------------------------------------------------------ */

describe('getTimeAgo', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2025-01-15T12:00:00Z'));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('returns "just now" for the current timestamp', () => {
    expect(getTimeAgo('2025-01-15T12:00:00Z')).toBe('just now');
  });

  const timeAgoCases: [string, string, string][] = [
    ['30 seconds ago', '2025-01-15T11:59:30Z', '30 seconds ago'],
    ['1 minute ago', '2025-01-15T11:59:00Z', '1 minute ago'],
    ['45 minutes ago', '2025-01-15T11:15:00Z', '45 minutes ago'],
    ['1 hour ago', '2025-01-15T11:00:00Z', '1 hour ago'],
    ['1 day ago', '2025-01-14T12:00:00Z', '1 day ago'],
    ['3 days ago', '2025-01-12T12:00:00Z', '3 days ago'],
    ['2 weeks ago', '2025-01-01T12:00:00Z', '2 weeks ago'],
    ['2 months ago', '2024-11-15T12:00:00Z', '2 months ago'],
    ['1 year ago', '2024-01-15T12:00:00Z', '1 year ago'],
  ];

  test.each(timeAgoCases)('%s', (_label, input, expected) => {
    expect(getTimeAgo(input)).toBe(expected);
  });
});

/* ------------------------------------------------------------------ */
/*  groupImagesByYearMonthFromMetadata                                */
/* ------------------------------------------------------------------ */

const makeImage = (
  id: string,
  dateCreated: string | null,
): Image => ({
  id,
  path: `/photos/${id}.jpg`,
  thumbnailPath: `/thumbs/${id}.jpg`,
  folder_id: 'folder-1',
  isTagged: false,
  metadata: {
    name: `${id}.jpg`,
    date_created: dateCreated,
    width: 1920,
    height: 1080,
    file_location: `/photos/${id}.jpg`,
    file_size: 1024,
    item_type: 'image/jpeg',
  } as ImageMetadata,
});

describe('groupImagesByYearMonthFromMetadata', () => {
  test('returns empty object for empty array', () => {
    expect(groupImagesByYearMonthFromMetadata([])).toEqual({});
  });

  test('groups images by year and month', () => {
    const images = [
      makeImage('a', '2024-03-10T10:00:00Z'),
      makeImage('b', '2024-03-20T10:00:00Z'),
      makeImage('c', '2024-11-05T10:00:00Z'),
      makeImage('d', '2023-01-01T10:00:00Z'),
    ];

    const result = groupImagesByYearMonthFromMetadata(images);

    expect(Object.keys(result)).toEqual(
      expect.arrayContaining(['2024', '2023']),
    );
    expect(result['2024']['03']).toHaveLength(2);
    expect(result['2024']['11']).toHaveLength(1);
    expect(result['2023']['01']).toHaveLength(1);
  });

  test('skips images with null date_created', () => {
    const images = [
      makeImage('a', '2024-06-15T10:00:00Z'),
      makeImage('b', null),
    ];

    const result = groupImagesByYearMonthFromMetadata(images);

    expect(result['2024']['06']).toHaveLength(1);
  });

  test('skips images with invalid date strings', () => {
    const images = [
      makeImage('a', '2024-06-15T10:00:00Z'),
      makeImage('b', 'not-a-date'),
    ];

    const result = groupImagesByYearMonthFromMetadata(images);

    const totalImages = Object.values(result).flatMap((months) =>
      Object.values(months).flat(),
    );
    expect(totalImages).toHaveLength(1);
  });
});
