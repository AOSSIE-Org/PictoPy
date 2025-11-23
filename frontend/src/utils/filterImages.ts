import { Image } from '@/types/Media';
import { FilterState } from '@/features/filterSlice';

/**
 * Normalizes a date string to YYYY-MM-DD format for consistent comparison.
 * Handles ISO format dates and various date string formats.
 *
 * @param dateString - Date string in various formats (ISO, etc.)
 * @returns Normalized date string in YYYY-MM-DD format, or empty string if invalid
 */
function normalizeDateToDay(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return '';
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
  } catch {
    return '';
  }
}

/**
 * Compares two date strings in YYYY-MM-DD format.
 *
 * @param date1 - First date string
 * @param date2 - Second date string
 * @returns -1 if date1 < date2, 0 if equal, 1 if date1 > date2
 */
function compareDates(date1: string, date2: string): number {
  if (date1 < date2) return -1;
  if (date1 > date2) return 1;
  return 0;
}

function normalizeTag(tag: string): string {
  return tag.trim().toLowerCase();
}

/**
 * Checks if an image matches the tag filter criteria.
 * Handles null, undefined, and empty arrays properly.
 * Uses case-insensitive partial matching.
 *
 * @param imageTags - Array of tags from the image (can be null, undefined, or empty array)
 * @param filterTags - Array of tags to filter by
 * @returns True if image matches tag filter, false otherwise
 */
function matchesTagFilter(imageTags: string[] | null | undefined, filterTags: string[]): boolean {
  if (!filterTags || filterTags.length === 0) {
    return true;
  }

  // Backend returns null for images without tags
  if (!imageTags || imageTags.length === 0) {
    return false;
  }

  const normalizedImageTags = imageTags.map(normalizeTag);
  const normalizedFilterTags = filterTags.map(normalizeTag);

  // Partial matching: "sun" matches "sunset"
  return normalizedFilterTags.some((filterTag) =>
    normalizedImageTags.some((imageTag) => imageTag.includes(filterTag))
  );
}

/**
 * Checks if an image's date falls within the specified date range.
 *
 * @param imageDate - Date string from image metadata
 * @param startDate - Start date filter (YYYY-MM-DD format, can be null)
 * @param endDate - End date filter (YYYY-MM-DD format, can be null)
 * @returns True if image date is within range, false otherwise
 */
function matchesDateRange(
  imageDate: string | null | undefined,
  startDate: string | null,
  endDate: string | null
): boolean {
  if (!imageDate) {
    return false;
  }

  const hasStartDate = startDate && startDate.trim() !== '';
  const hasEndDate = endDate && endDate.trim() !== '';

  if (!hasStartDate && !hasEndDate) {
    return true;
  }

  try {
    const imageDateNormalized = normalizeDateToDay(imageDate);

    if (!imageDateNormalized) {
      return false;
    }

    if (hasStartDate) {
      const startDateNormalized = startDate!.trim();
      if (compareDates(imageDateNormalized, startDateNormalized) < 0) {
        return false;
      }
    }

    if (hasEndDate) {
      const endDateNormalized = endDate!.trim();
      if (compareDates(imageDateNormalized, endDateNormalized) > 0) {
        return false;
      }
    }

    return true;
  } catch (error) {
    console.warn('Date range filter error:', error);
    return false;
  }
}

function matchesFileSizeFilter(
  fileSizeBytes: number | undefined,
  minSizeMB: number | null,
  maxSizeMB: number | null
): boolean {
  const hasMinFilter = minSizeMB !== null;
  const hasMaxFilter = maxSizeMB !== null;

  if (!hasMinFilter && !hasMaxFilter) {
    return true;
  }

  const fileSizeMB = (fileSizeBytes || 0) / (1024 * 1024);

  if (hasMinFilter && fileSizeMB < minSizeMB!) {
    return false;
  }

  if (hasMaxFilter && fileSizeMB > maxSizeMB!) {
    return false;
  }

  return true;
}

function matchesFileTypeFilter(
  imageType: string | undefined,
  filterTypes: string[]
): boolean {
  if (filterTypes.length === 0) {
    return true;
  }

  if (!imageType) {
    return false;
  }

  return filterTypes.includes(imageType);
}

/**
 * Filters an array of images based on the provided filter criteria.
 * All filters are applied with AND logic (image must match all active filters).
 *
 * @param images - Array of images to filter
 * @param filters - Filter state containing all filter criteria
 * @returns Filtered array of images that match all criteria
 */
export function filterImages(images: Image[], filters: FilterState): Image[] {
  return images.filter((image) => {
    if (filters.tags.length > 0) {
      if (!matchesTagFilter(image.tags, filters.tags)) {
        return false;
      }
    }

    if (filters.isFavourite !== null) {
      if (image.isFavourite !== filters.isFavourite) {
        return false;
      }
    }

    if (filters.isTagged !== null) {
      if (image.isTagged !== filters.isTagged) {
        return false;
      }
    }

    const hasDateFilter =
      (filters.dateRange.start && filters.dateRange.start.trim() !== '') ||
      (filters.dateRange.end && filters.dateRange.end.trim() !== '');

    if (hasDateFilter) {
      if (
        !matchesDateRange(
          image.metadata?.date_created,
          filters.dateRange.start,
          filters.dateRange.end
        )
      ) {
        return false;
      }
    }

    const hasFileSizeFilter =
      filters.fileSize.min !== null || filters.fileSize.max !== null;

    if (hasFileSizeFilter) {
      if (
        !matchesFileSizeFilter(
          image.metadata?.file_size,
          filters.fileSize.min,
          filters.fileSize.max
        )
      ) {
        return false;
      }
    }

    if (filters.fileTypes.length > 0) {
      if (!matchesFileTypeFilter(image.metadata?.item_type, filters.fileTypes)) {
        return false;
      }
    }

    return true;
  });
}