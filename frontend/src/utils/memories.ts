import { convertFileSrc } from '@tauri-apps/api/core';
import type {
  MemoryCard,
  MemoryEventType,
  MemoryImage,
  MemoryStory,
  MemoryVideo,
} from '@/api/api-functions/memories';

export const MEMORY_PLACEHOLDER_IMAGE = '/photo.png';

/** Resolve a stored file path to something an `<img>` can load. */
export const getMemoryImageUrl = (path: string | null | undefined): string => {
  if (!path) return MEMORY_PLACEHOLDER_IMAGE;
  return convertFileSrc(path);
};

/** Thumbnail URL for a curated image, falling back to the full-size path. */
export const getThumbnailUrl = (image: MemoryImage): string =>
  getMemoryImageUrl(image.thumbnailPath ?? image.path);

/** Cover thumbnail URL for a memory card. */
export const getCoverUrl = (memory: MemoryCard): string =>
  getMemoryImageUrl(memory.cover_thumbnail_path);

/** Format an ISO date as e.g. "26 July 2024". */
export const formatMemoryDate = (isoDate: string | null): string => {
  if (!isoDate) return '';
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

/**
 * Format a memory's span, collapsing a single day and a single month.
 */
export const formatDateRange = (
  startDate: string | null,
  endDate: string | null,
): string => {
  if (!startDate) return '';

  const start = new Date(startDate);
  if (Number.isNaN(start.getTime())) return '';

  const end = endDate ? new Date(endDate) : start;
  if (
    Number.isNaN(end.getTime()) ||
    start.toDateString() === end.toDateString()
  )
    return formatMemoryDate(startDate);

  if (
    start.getFullYear() === end.getFullYear() &&
    start.getMonth() === end.getMonth()
  ) {
    const monthYear = start.toLocaleDateString(undefined, {
      month: 'long',
      year: 'numeric',
    });
    return `${start.getDate()}–${end.getDate()} ${monthYear}`;
  }

  const startLabel = start.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
  const endLabel = end.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  return `${startLabel} – ${endLabel}`;
};

/** Format a photo count for display. */
export const formatPhotoCount = (count: number): string =>
  count === 1 ? '1 photo' : `${count} photos`;

const EVENT_TYPE_LABELS: Record<MemoryEventType, string> = {
  anniversary: 'On this day',
  import_event: 'Event',
  semantic_event: 'Highlight',
};

/** Human-readable badge text for a memory's trigger. */
export const formatEventType = (eventType: MemoryEventType): string =>
  EVENT_TYPE_LABELS[eventType] ?? 'Memory';

/** The curator's subtitle when it set one, otherwise the date span. */
export const formatMemorySubtitle = (memory: MemoryCard): string =>
  memory.subtitle ||
  formatDateRange(memory.period_start, memory.period_end) ||
  formatMemoryDate(memory.surface_date);

// A union, not a widened image type: the viewer renders two different elements
// and holds a video slide for its own length.
export type MemorySlide =
  | ({ kind: 'image' } & MemoryImage)
  | ({ kind: 'video' } & MemoryVideo);

// Two arrays because they live in two tables, but sort_order is one sequence
// across both -- so this merges rather than concatenates.
export const buildMemorySlides = (
  memory: Pick<MemoryStory, 'images' | 'videos'> | null | undefined,
): MemorySlide[] => {
  if (!memory) return [];
  const slides: MemorySlide[] = [
    ...(memory.images ?? []).map((image) => ({
      kind: 'image' as const,
      ...image,
    })),
    ...(memory.videos ?? []).map((video) => ({
      kind: 'video' as const,
      ...video,
    })),
  ];
  return slides.sort((a, b) => a.sort_order - b.sort_order);
};

// A clip is held for its recorded length rather than cut off mid-shot or left
// on a frozen last frame. A still gets the configured interval.
export const slideDurationMs = (
  slide: MemorySlide | undefined,
  photoDurationMs: number,
): number => {
  if (slide?.kind === 'video' && slide.duration && slide.duration > 0) {
    return slide.duration * 1000;
  }
  return photoDurationMs;
};
