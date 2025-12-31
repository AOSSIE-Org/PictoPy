import axios from 'axios';
import { Memory, MemoryListResponse, GenerateMemoriesResponse } from '../types/memory';

const API_BASE_URL = 'http://localhost:8000'\;

export const memoriesApi = {
  /**
   * Get all memories
   */
  async getMemories(limit?: number): Promise<MemoryListResponse> {
    const response = await axios.get<MemoryListResponse>(`${API_BASE_URL}/memories`, {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Get a specific memory by ID
   */
  async getMemoryById(memoryId: string): Promise<Memory> {
    const response = await axios.get<Memory>(`${API_BASE_URL}/memories/${memoryId}`);
    return response.data;
  },

  /**
   * Generate new memories from images
   */
  async generateMemories(): Promise<GenerateMemoriesResponse> {
    const response = await axios.post<GenerateMemoriesResponse>(
      `${API_BASE_URL}/memories/generate`
    );
    return response.data;
  },

  /**
   * Delete a memory
   */
  async deleteMemory(memoryId: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/memories/${memoryId}`);
  },

  /**
   * Mark a memory as viewed
   */
  async markMemoryViewed(memoryId: string): Promise<void> {
    await axios.post(`${API_BASE_URL}/memories/${memoryId}/view`);
  },
};
