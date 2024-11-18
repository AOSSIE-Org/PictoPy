// Media.ts

import { MediaItem } from '@/types/Media';

export function sortMedia(
  mediaItems: MediaItem[],
  sortBy: string,
): MediaItem[] {
  return [...mediaItems].sort((a, b) => {
    const aDate = a.date ? new Date(a.date) : new Date();
    const bDate = b.date ? new Date(b.date) : new Date();

    if (sortBy === 'date') {
      return 0;
    } else if (sortBy.startsWith('year-')) {
      const year = parseInt(sortBy.split('-')[1]);
      const aYear = aDate.getFullYear();
      const bYear = bDate.getFullYear();

      if (aYear === year && bYear !== year) return -1;
      if (bYear === year && aYear !== year) return 1;
      if (aYear === bYear) {
        // If both are from the same year, sort by date
        return bDate.getTime() - aDate.getTime();
      }
      // If neither or both are from the selected year, maintain original order
      return 0;
    } else {
      console.warn(
        `Invalid sortBy option: ${sortBy}. Defaulting to date sorting.`,
      );
      return bDate.getTime() - aDate.getTime();
    }
  });
}
