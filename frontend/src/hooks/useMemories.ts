import { useState, useEffect, useCallback } from 'react';
import { Memory, MemoryListResponse } from '../types/memory';
import { memoriesApi } from '../api/memories';

export const useMemories = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMemories = useCallback(async (limit?: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await memoriesApi.getMemories(limit);
      setMemories(response.memories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch memories');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const generateMemories = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await memoriesApi.generateMemories();
      // Refresh memories after generation
      await fetchMemories();
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate memories');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchMemories]);

  const deleteMemory = useCallback(async (memoryId: string) => {
    try {
      await memoriesApi.deleteMemory(memoryId);
      // Remove from local state
      setMemories((prev) => prev.filter((m) => m.id !== memoryId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete memory');
      throw err;
    }
  }, []);

  const markMemoryViewed = useCallback(async (memoryId: string) => {
    try {
      await memoriesApi.markMemoryViewed(memoryId);
    } catch (err) {
      console.error('Failed to mark memory as viewed:', err);
    }
  }, []);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  return {
    memories,
    isLoading,
    error,
    fetchMemories,
    generateMemories,
    deleteMemory,
    markMemoryViewed,
  };
};
