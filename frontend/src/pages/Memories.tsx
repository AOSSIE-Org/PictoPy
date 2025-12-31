/**
 * Memories Page Component
 * 
 * Displays automatically generated memories based on time and location.
 * Memories are presented as interactive cards that users can explore.
 */

import React, { useEffect, useState } from 'react';
import { memoriesApi } from '../services/memoriesApi';
import { Memory } from '../types/memories';
import MemoryCard from '../components/memories/MemoryCard';
import MemoryDetail from '../components/memories/MemoryDetail';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import { Button } from '../components/ui/button';
import { RefreshCw, Sparkles } from 'lucide-react';

const MemoriesPage: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await memoriesApi.listMemories();
      setMemories(data.memories);
    } catch (err) {
      setError('Failed to load memories. Please try again.');
      console.error('Error loading memories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMemories = async () => {
    try {
      setGenerating(true);
      setError(null);
      await memoriesApi.generateMemories({
        include_time_based: true,
        include_location_based: true,
        min_images_for_location: 5,
        distance_threshold: 0.05
      });
      await loadMemories();
    } catch (err) {
      setError('Failed to generate memories. Please try again.');
      console.error('Error generating memories:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError(null);
      await memoriesApi.refreshMemories();
      await loadMemories();
    } catch (err) {
      setError('Failed to refresh memories. Please try again.');
      console.error('Error refreshing memories:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleMemoryClick = async (memory: Memory) => {
    try {
      // Load full memory details
      const fullMemory = await memoriesApi.getMemory(memory.id!);
      setSelectedMemory(fullMemory);
    } catch (err) {
      console.error('Error loading memory details:', err);
    }
  };

  const handleCloseDetail = () => {
    setSelectedMemory(null);
  };

  const handleDeleteMemory = async (memoryId: number) => {
    try {
      await memoriesApi.deleteMemory(memoryId);
      setMemories(memories.filter(m => m.id !== memoryId));
      setSelectedMemory(null);
    } catch (err) {
      setError('Failed to delete memory. Please try again.');
      console.error('Error deleting memory:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
        <p className="ml-4 text-lg">Loading your memories...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-purple-500" />
            Memories
          </h1>
          <p className="text-gray-600">
            Relive your moments through time and places
          </p>
        </div>
        
        <div className="flex gap-3">
          {memories.length > 0 && (
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              variant="outline"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          )}
          
          <Button
            onClick={handleGenerateMemories}
            disabled={generating}
            variant="default"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            {memories.length === 0 ? 'Generate Memories' : 'Generate New'}
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <ErrorMessage message={error} onDismiss={() => setError(null)} />
      )}

      {/* Memories Grid */}
      {memories.length === 0 && !generating ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Sparkles className="w-16 h-16 text-gray-300 mb-4" />
          <h2 className="text-2xl font-semibold text-gray-700 mb-2">
            No Memories Yet
          </h2>
          <p className="text-gray-500 mb-6 text-center max-w-md">
            Start creating memories by clicking the "Generate Memories" button above.
            We'll automatically find special moments from your photos based on time and location.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {memories.map((memory) => (
            <MemoryCard
              key={memory.id}
              memory={memory}
              onClick={() => handleMemoryClick(memory)}
            />
          ))}
        </div>
      )}

      {/* Loading State for Generation */}
      {generating && (
        <div className="flex flex-col items-center justify-center py-20">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-lg text-gray-600">
            Generating your memories...
          </p>
          <p className="text-sm text-gray-500 mt-2">
            This may take a moment as we analyze your photos
          </p>
        </div>
      )}

      {/* Memory Detail Modal */}
      {selectedMemory && (
        <MemoryDetail
          memory={selectedMemory}
          onClose={handleCloseDetail}
          onDelete={handleDeleteMemory}
        />
      )}
    </div>
  );
};

export default MemoriesPage;
