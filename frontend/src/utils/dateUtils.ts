import { Image } from '@/types/Media';

export const getTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const secondsAgo = Math.floor((now.getTime() - date.getTime()) / 1000);

  const timeFormats = [
    { limit: 60, unit: 'second', divisor: 1 },
    { limit: 3600, unit: 'minute', divisor: 60 },
    { limit: 86400, unit: 'hour', divisor: 3600 },
    { limit: 604800, unit: 'day', divisor: 86400 },
    { limit: 2592000, unit: 'week', divisor: 604800 },
    { limit: 31536000, unit: 'month', divisor: 2592000 },
    { limit: Infinity, unit: 'year', divisor: 31536000 },
  ];

  for (const format of timeFormats) {
    if (secondsAgo < format.limit) {
      const value = Math.floor(secondsAgo / format.divisor);
      return value <= 0
        ? 'just now'
        : `${value} ${format.unit}${value > 1 ? 's' : ''} ago`;
    }
  }

  return 'a long time ago';
};

// To group Images from same Month & Year.
export const groupImagesByYearMonthFromMetadata = (images: Image[]) => {
  const grouped: Record<string, Record<string, Image[]>> = {};

  images.forEach((image) => {
    const dateStr = image.metadata?.date_created; // extract date from metadata.date_created
    if (!dateStr) return;

    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return;

    const year = date.getFullYear().toString();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');

    if (!grouped[year]) {
      grouped[year] = {};
    }
    if (!grouped[year][month]) {
      grouped[year][month] = [];
    }

    grouped[year][month].push(image);
  });

  return grouped;
};
