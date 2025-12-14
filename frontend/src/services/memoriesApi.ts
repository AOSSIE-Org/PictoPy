/**
 * Memories API Service
 * 
 * Handles all HTTP requests to the memories backend endpoints.
 * Provides type-safe interfaces and error handling.
 */

import axios, { AxiosError } from 'axios';
import { convertFileSrc } from '@tauri-apps/api/core';
import { BACKEND_URL } from '@/config/Backend';

const API_BASE_URL = `${BACKEND_URL}/api/memories`;

// ============================================================================
// TypeScript Interfaces
// ============================================================================

/**
 * Individual image within a memory
 */
export interface MemoryImage {
  id: string;
  path: string;
  thumbnailPath: string;
  latitude: number | null;
  longitude: number | null;
  captured_at: string | null; // ISO 8601 format
}

/**
 * Memory object representing a collection of photos
 */
export interface Memory {
  memory_id: string;
  title: string;
  description: string;
  location_name: string;
  date_start: string | null; // ISO 8601 format
  date_end: string | null; // ISO 8601 format
  image_count: number;
  images: MemoryImage[];
  thumbnail_image_id: string;
  center_lat: number;
  center_lon: number;
}

/**
 * Response from POST /api/memories/generate
 */
export interface GenerateMemoriesResponse {
  success: boolean;
  message: string;
  memory_count: number;
  image_count: number;
  memories: Memory[];
}

/**
 * Response from GET /api/memories/timeline
 */
export interface TimelineResponse {
  success: boolean;
  date_range: {
    start: string;
    end: string;
  };
  memory_count: number;
  memories: Memory[];
}

/**
 * Response from GET /api/memories/on-this-day
 */
export interface OnThisDayResponse {
  success: boolean;
  today: string; // e.g., "December 14"
  years: number[]; // [2024, 2023, 2022]
  image_count: number;
  images: MemoryImage[];
}

/**
 * Location cluster with sample images
 */
export interface LocationCluster {
  location_name: string;
  center_lat: number;
  center_lon: number;
  image_count: number;
  sample_images: MemoryImage[];
}

/**
 * Response from GET /api/memories/locations
 */
export interface LocationsResponse {
  success: boolean;
  location_count: number;
  locations: LocationCluster[];
}

/**
 * API Error structure
 */
export interface ApiError {
  message: string;
  status?: number;
  details?: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Generate all memories from images with location data
 * 
 * @param options - Clustering parameters
 * @returns Generated memories
 */
export const generateMemories = async (options?: {
  location_radius_km?: number;
  date_tolerance_days?: number;
  min_images?: number;
}): Promise<GenerateMemoriesResponse> => {
  try {
    const params = new URLSearchParams();
    if (options?.location_radius_km) params.append('location_radius_km', options.location_radius_km.toString());
    if (options?.date_tolerance_days) params.append('date_tolerance_days', options.date_tolerance_days.toString());
    if (options?.min_images) params.append('min_images', options.min_images.toString());

    const response = await axios.post<GenerateMemoriesResponse>(
      `${API_BASE_URL}/generate${params.toString() ? '?' + params.toString() : ''}`
    );

    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get memories from the past N days as a timeline
 * 
 * @param days - Number of days to look back (default: 365)
 * @param options - Clustering parameters
 * @returns Timeline memories
 */
export const getTimeline = async (
  days: number = 365,
  options?: {
    location_radius_km?: number;
    date_tolerance_days?: number;
  }
): Promise<TimelineResponse> => {
  try {
    const params = new URLSearchParams();
    params.append('days', days.toString());
    if (options?.location_radius_km) params.append('location_radius_km', options.location_radius_km.toString());
    if (options?.date_tolerance_days) params.append('date_tolerance_days', options.date_tolerance_days.toString());

    const response = await axios.get<TimelineResponse>(
      `${API_BASE_URL}/timeline?${params.toString()}`
    );

    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get photos taken on this date in previous years
 * 
 * @returns On This Day images
 */
export const getOnThisDay = async (): Promise<OnThisDayResponse> => {
  try {
    const response = await axios.get<OnThisDayResponse>(
      `${API_BASE_URL}/on-this-day`
    );

    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get all unique locations where photos were taken
 * 
 * @param options - Clustering and sampling parameters
 * @returns Location clusters
 */
export const getLocations = async (options?: {
  location_radius_km?: number;
  max_sample_images?: number;
}): Promise<LocationsResponse> => {
  try {
    const params = new URLSearchParams();
    if (options?.location_radius_km) params.append('location_radius_km', options.location_radius_km.toString());
    if (options?.max_sample_images) params.append('max_sample_images', options.max_sample_images.toString());

    const response = await axios.get<LocationsResponse>(
      `${API_BASE_URL}/locations${params.toString() ? '?' + params.toString() : ''}`
    );

    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Convert Axios errors to our ApiError format
 */
const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    
    return {
      message: axiosError.response?.data?.message || 
               axiosError.response?.data?.detail || 
               axiosError.message || 
               'An unknown error occurred',
      status: axiosError.response?.status,
      details: axiosError.response?.statusText
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message
    };
  }

  return {
    message: 'An unexpected error occurred'
  };
};

// ============================================================================
// Utility Functions
// ============================================================================

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
      day: 'numeric'
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
export const formatDateRange = (startDate: string | null, endDate: string | null): string => {
  if (!startDate || !endDate) return 'Unknown date';

  try {
    const start = new Date(startDate);
    const end = new Date(endDate);

    // Same day
    if (start.toDateString() === end.toDateString()) {
      return start.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    }

    // Same month and year
    if (start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear()) {
      const monthYear = start.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
      return `${start.getDate()} - ${end.getDate()}, ${monthYear}`;
    }

    // Different months or years
    const startFormatted = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endFormatted = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    return `${startFormatted} - ${endFormatted}`;
  } catch {
    return 'Invalid date range';
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
 * Format date range with relative time for recent dates
 * 
 * @param startDate - Start date ISO string
 * @param endDate - End date ISO string
 * @returns Formatted range with relative dates like "Yesterday", "Last week", "2 months ago"
 */
export const formatDateRangeRelative = (startDate: string | null, endDate: string | null): string => {
  if (!startDate || !endDate) return 'Unknown date';

  try {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const now = new Date();
    
    // Calculate days difference from end date
    const daysDiff = Math.floor((now.getTime() - end.getTime()) / (1000 * 60 * 60 * 24));
    
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
    return start.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  } catch {
    return formatDateRange(startDate, endDate);
  }
};

/**
 * Generate a human-readable title from location and date
 * Improves ugly coordinate-based titles like "26.9333°, 75.9228° - November 2025"
 * 
 * @param memory - Memory object with location and date info
 * @returns Better title like "Weekend in Jaipur", "Jaipur Trip", or "December 2024"
 */
export const generateMemoryTitle = (memory: Memory): string => {
  const location = memory.location_name;
  const imageCount = memory.image_count;
  
  // Check if it's a date-based memory (no GPS data)
  if (location === 'Date-Based Memory') {
    // Use the title from backend which is already well-formatted for date-only memories
    return memory.title;
  }
  
  // If location doesn't look like coordinates, use it
  if (!location.includes('°') && !location.match(/^-?\d+\.\d+/)) {
    // Parse city name from location (e.g., "Jaipur, Rajasthan" -> "Jaipur")
    const cityName = location.split(',')[0].trim();
    
    // Add descriptive word based on image count
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
    const monthYear = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    return `Memories from ${monthYear}`;
  }
  
  // Last resort
  return memory.title || 'Photo Collection';
};

/**
 * Format location name by removing coordinates if present
 * 
 * @param locationName - Raw location name from API
 * @returns Cleaned location name or empty string if only coordinates or date-based
 */
export const formatLocationName = (locationName: string): string => {
  // Hide date-based memories indicator (backend sends "Date-Based Memory")
  if (locationName === 'Date-Based Memory') {
    return '';
  }
  
  // If it looks like coordinates (contains ° or is a number pattern), hide it
  if (locationName.includes('°') || locationName.match(/^-?\d+\.\d+.*-?\d+\.\d+/)) {
    return ''; // Hide ugly coordinates
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
  // Use Tauri's convertFileSrc for proper file path handling in desktop app
  if (image.thumbnailPath) {
    return convertFileSrc(image.thumbnailPath);
  }
  
  // Fallback to placeholder
  return '/photo.png';
};
