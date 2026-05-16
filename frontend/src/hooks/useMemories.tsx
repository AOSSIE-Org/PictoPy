import { usePictoQuery } from '@/hooks/useQueryExtension';
import {
  generateMemories,
  getTimeline,
  getOnThisDay,
} from '@/api/api-functions/memories';

/**
 * Custom hook for fetching all memories
 */
export const useAllMemories = () => {
  return usePictoQuery({
    queryKey: ['memories', 'all'],
    queryFn: () => generateMemories(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Custom hook for fetching recent memories (last N days)
 */
export const useRecentMemories = (days: number = 30) => {
  return usePictoQuery({
    queryKey: ['memories', 'recent', days],
    queryFn: () => getTimeline(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Custom hook for fetching year memories
 */
export const useYearMemories = (days: number = 365) => {
  return usePictoQuery({
    queryKey: ['memories', 'year', days],
    queryFn: () => getTimeline(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Custom hook for fetching "On This Day" images
 */
export const useOnThisDay = () => {
  return usePictoQuery({
    queryKey: ['memories', 'onThisDay'],
    queryFn: () => getOnThisDay(),
    staleTime: 60 * 60 * 1000, // 1 hour (this data is date-specific)
  });
};
