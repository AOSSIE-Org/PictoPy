import { useEffect, useMemo, useState } from 'react';

interface Image {
  id: string;
  date: string;
  title: string;
  popularity: number;
  src: string;
  tags: string[];
}

function useSortedImages(data: any): Image[] {
  const [sortedImages, setSortedImages] = useState<Image[]>([]);

  useEffect(() => {
    const parseAndSortImageData = (data: any): Image[] => {
      const images: Image[] = [];

      for (const filePath in data) {
        if (Object.prototype.hasOwnProperty.call(data, filePath)) {
          const tags = data[filePath].split(', ');
          const fileName = filePath.substring(filePath.lastIndexOf('/') + 1);

          const image: Image = {
            id: fileName,
            date: '',
            title: data[filePath],
            popularity: tags.length,
            src: filePath,
            tags: tags,
          };

          images.push(image);
        }
      }

      images.sort((a, b) => b.popularity - a.popularity);

      return images;
    };

    const sortedImages = parseAndSortImageData(data);

    setSortedImages(sortedImages);
  }, []);

  return sortedImages;
}

export default useSortedImages;

export interface MediaItem {
  src: string;
  date: string;
  title?: string;
}

type SortBy = 'date' | `year-${string}`;

export function useSortMedia(mediaItems: MediaItem[]) {
  const [sortBy, setSortBy] = useState<SortBy>('date');

  const sortedMedia = useMemo(() => {
    const sortedItems = [...mediaItems];

    if (sortBy === 'date') {
      return sortedItems.sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
      );
    } else if (sortBy.startsWith('year-')) {
      const year = sortBy.split('-')[1];
      return sortedItems
        .filter((item) => new Date(item.date).getFullYear().toString() === year)
        .sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
        );
    }

    return sortedItems;
  }, [mediaItems, sortBy]);

  const availableYears = useMemo(() => {
    const years = new Set<string>();
    mediaItems.forEach((item) => {
      const year = new Date(item.date).getFullYear().toString();
      years.add(year);
    });
    return Array.from(years).sort((a, b) => parseInt(b) - parseInt(a));
  }, [mediaItems]);

  return {
    sortBy,
    setSortBy,
    sortedMedia,
    availableYears,
  };
}
