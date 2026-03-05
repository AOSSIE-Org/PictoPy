/**
 * Memories Utility Functions
 *
 * Pure utility functions for formatting and processing memory data.
 */

import { convertFileSrc } from '@tauri-apps/api/core';
import { Memory, MemoryImage } from '@/api/api-functions/memories';

/**
 * Format a date string to human-readable format
 *
 * @param isoDate - ISO 8601 date string
 * @returns Formatted date (e.g., "November 25, 2025")
 */
export const formatMemoryDate = (isoDate: string | null): string => {
  if (!isoDate) return 'Unknown date';

  try {
    const date = new Date(isoDate);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return 'Invalid date';
  }
};

/**
 * Format date range for memory display
 *
 * @param startDate - Start date ISO string
 * @param endDate - End date ISO string
 * @returns Formatted range (e.g., "Nov 25 - Nov 27, 2025")
 */
export const formatDateRange = (
  startDate: string | null,
  endDate: string | null,
): string => {
  if (!startDate || !endDate) return 'Unknown date';

  try {
    const start = new Date(startDate);
    const end = new Date(endDate);

    // Same day
    if (start.toDateString() === end.toDateString()) {
      return start.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    }

    // Same month and year
    if (
      start.getMonth() === end.getMonth() &&
      start.getFullYear() === end.getFullYear()
    ) {
      const monthYear = start.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      });
      return `${start.getDate()} - ${end.getDate()}, ${monthYear}`;
    }

    // Different months or years
    const startFormatted = start.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
    const endFormatted = end.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
    return `${startFormatted} - ${endFormatted}`;
  } catch {
    return 'Invalid date range';
  }
};

/**
 * Format date range with relative time for recent dates
 *
 * @param startDate - Start date ISO string
 * @param endDate - End date ISO string
 * @returns Formatted range with relative dates like "Yesterday", "Last week", "2 months ago"
 */
export const formatDateRangeRelative = (
  startDate: string | null,
  endDate: string | null,
): string => {
  if (!startDate || !endDate) return 'Unknown date';

  try {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const now = new Date();

    // Calculate days difference from end date
    const daysDiff = Math.floor(
      (now.getTime() - end.getTime()) / (1000 * 60 * 60 * 24),
    );

    // Today
    if (daysDiff === 0) {
      return 'Today';
    }

    // Yesterday
    if (daysDiff === 1) {
      return 'Yesterday';
    }

    // This week (2-6 days ago)
    if (daysDiff >= 2 && daysDiff <= 6) {
      return `${daysDiff} days ago`;
    }

    // Last week
    if (daysDiff >= 7 && daysDiff <= 13) {
      return 'Last week';
    }

    // This month (2-4 weeks ago)
    if (daysDiff >= 14 && daysDiff <= 30) {
      const weeks = Math.floor(daysDiff / 7);
      return `${weeks} weeks ago`;
    }

    // Recent months (1-12 months ago)
    const monthsDiff = Math.floor(daysDiff / 30);
    if (monthsDiff >= 1 && monthsDiff <= 11) {
      return monthsDiff === 1 ? 'Last month' : `${monthsDiff} months ago`;
    }

    // Over a year ago - show month and year
    return start.toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return formatDateRange(startDate, endDate);
  }
};

/**
 * Calculate years ago from a date
 *
 * @param isoDate - ISO date string
 * @returns Number of years ago
 */
export const calculateYearsAgo = (isoDate: string): number => {
  try {
    const date = new Date(isoDate);
    const now = new Date();
    return now.getFullYear() - date.getFullYear();
  } catch {
    return 0;
  }
};

/**
 * Format photo count
 *
 * @param count - Number of photos
 * @returns Formatted string (e.g., "1 photo" or "5 photos")
 */
export const formatPhotoCount = (count: number): string => {
  return count === 1 ? '1 photo' : `${count} photos`;
};

/**
 * Generate a human-readable title from location and date
 *
 * @param memory - Memory object with location and date info
 * @returns Better title like "Weekend in Jaipur", "Jaipur Trip", or "December 2024"
 */
export const generateMemoryTitle = (memory: Memory): string => {
  const location = memory.location_name;
  const imageCount = memory.image_count;

  // Check if it's a date-based memory (no GPS data)
  if (location === 'Date-Based Memory') {
    return memory.title;
  }

  // If location doesn't look like coordinates, use it
  if (!location.includes('°') && !location.match(/^-?\d+\.\d+/)) {
    const cityName = location.split(',')[0].trim();

    if (imageCount >= 50) {
      return `${cityName} Adventure`;
    } else if (imageCount >= 20) {
      return `${cityName} Trip`;
    } else if (imageCount >= 10) {
      return `Weekend in ${cityName}`;
    } else {
      return `${cityName} Memories`;
    }
  }

  // Fallback: coordinates - try to make it cleaner
  if (memory.date_start) {
    const date = new Date(memory.date_start);
    const monthYear = date.toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric',
    });
    return `Memories from ${monthYear}`;
  }

  return memory.title || 'Photo Collection';
};

/**
 * Format location name by removing coordinates if present
 *
 * @param locationName - Raw location name from API
 * @returns Cleaned location name or empty string if only coordinates or date-based
 */
export const formatLocationName = (locationName: string): string => {
  if (locationName === 'Date-Based Memory') {
    return '';
  }

  if (
    locationName.includes('°') ||
    locationName.match(/^-?\d+\.\d+.*-?\d+\.\d+/)
  ) {
    return '';
  }

  return locationName;
};

/**
 * Get thumbnail URL with fallback
 *
 * @param image - Memory image object
 * @returns Thumbnail URL or placeholder
 */
export const getThumbnailUrl = (image: MemoryImage): string => {
  if (image.thumbnailPath) {
    return convertFileSrc(image.thumbnailPath);
  }
  return '/photo.png';
};
