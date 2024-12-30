// Media.ts

import { MediaItem } from '@/types/Media';

export function sortMedia(
  mediaItems: MediaItem[],
  sortBy: string[],
): MediaItem[] {
  return [...mediaItems].sort((a, b) => {
    for (const criterion of sortBy) {
      const aDate = a.date ? new Date(a.date) : new Date();
      const bDate = b.date ? new Date(b.date) : new Date();

      switch (criterion) {
        case 'date':
          // Sort by date (most recent first)
          if (bDate.getTime() !== aDate.getTime()) {
            return bDate.getTime() - aDate.getTime();
          }
          break;

        case 'name':
        case 'asc':
          // Sort alphabetically by file name
          //@ts-ignore
          const nameCompareAsc = a.title.localeCompare(b.title);
          if (nameCompareAsc !== 0) return nameCompareAsc;
          break;

        case 'desc':
          // Sort alphabetically by file name in descending order
          //@ts-ignore

          const nameCompareDesc = b.title.localeCompare(a.title);
          if (nameCompareDesc !== 0) return nameCompareDesc;
          break;

        case 'size':
          // Assuming `size` is a property in MediaItem (in bytes, KB, etc.)
          //@ts-ignore

          if (a.size && b.size && a.size !== b.size) {
            //@ts-ignore

            return a.size - b.size;
          }
          break;

        case 'type':
          // Assuming `type` refers to file extension or media type
          const aType = a.original?.split('.').pop()?.toLowerCase() || '';
          const bType = b.original?.split('.').pop()?.toLowerCase() || '';
          const typeCompare = aType.localeCompare(bType);
          if (typeCompare !== 0) return typeCompare;
          break;

        default:
          console.warn(`Invalid sortBy option: ${criterion}. Skipping.`);
          break;
      }
    }
    // If all criteria result in equality, maintain original order
    return 0;
  });
}
