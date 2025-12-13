/**
 * API service for Memories feature
 * 
 * Provides functions to interact with the memories backend API.
 */

import axios from 'axios';
import {
  Memory,
  MemoriesListResponse,
  GenerateMemoriesRequest,
  GenerateMemoriesResponse,
  DeleteMemoryResponse
} from '../types/memories';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const memoriesApi = {
  /**
   * Generate new memories based on time and location
   */
  async generateMemories(
    request: GenerateMemoriesRequest
  ): Promise<GenerateMemoriesResponse> {
    const response = await api.post<GenerateMemoriesResponse>(
      '/memories/generate',
      request
    );
    return response.data;
  },

  /**
   * Get list of all memories
   */
  async listMemories(): Promise<MemoriesListResponse> {
    const response = await api.get<MemoriesListResponse>('/memories/list');
    return response.data;
  },

  /**
   * Get details of a specific memory
   */
  async getMemory(memoryId: number): Promise<Memory> {
    const response = await api.get<Memory>(`/memories/${memoryId}`);
    return response.data;
  },

  /**
   * Delete a specific memory
   */
  async deleteMemory(memoryId: number): Promise<DeleteMemoryResponse> {
    const response = await api.delete<DeleteMemoryResponse>(
      '/memories/delete',
      {
        data: { memory_id: memoryId }
      }
    );
    return response.data;
  },

  /**
   * Refresh all memories (regenerate from scratch)
   */
  async refreshMemories(): Promise<GenerateMemoriesResponse> {
    const response = await api.post<GenerateMemoriesResponse>(
      '/memories/refresh'
    );
    return response.data;
  },
};
