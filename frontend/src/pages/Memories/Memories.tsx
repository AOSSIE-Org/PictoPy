import React, { useState } from 'react';
import { useMemories } from '../../hooks/useMemories';
import { MemoryCard } from '../../components/MemoryCard';
import { Memory } from '../../types/memory';

const Memories: React.FC = () => {
  const { memories, isLoading, error, generateMemories } = useMemories();
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

  const handleGenerateMemories = async () => {
    setIsGenerating(true);
    try {
      const result = await generateMemories();
      alert(result.message);
    } catch (err) {
      alert('Failed to generate memories');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleMemoryClick = (memory: Memory) => {
    setSelectedMemory(memory);
  };

  if (isLoading && memories.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading memories...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              ✨ Memories
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Relive your special moments from the past
            </p>
          </div>
          <button
            onClick={handleGenerateMemories}
            disabled={isGenerating}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? 'Generating...' : '🔄 Generate Memories'}
          </button>
        </div>
      </div>

      {/* Memories Grid */}
      {memories.length === 0 ? (
        <div className="max-w-7xl mx-auto text-center py-20">
          <div className="text-6xl mb-4">📸</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            No Memories Yet
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Generate memories from your photos to see them here
          </p>
          <button
            onClick={handleGenerateMemories}
            disabled={isGenerating}
            className="px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all"
          >
            {isGenerating ? 'Generating...' : 'Generate Your First Memories'}
          </button>
        </div>
      ) : (
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {memories.map((memory) => (
            <MemoryCard
              key={memory.id}
              memory={memory}
              onClick={() => handleMemoryClick(memory)}
            />
          ))}
        </div>
      )}

      {/* Memory Detail Modal (Simple) */}
      {selectedMemory && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedMemory(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full p-8 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              {selectedMemory.title}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {selectedMemory.description}
            </p>
            <div className="text-sm text-gray-500 dark:text-gray-400 space-y-2">
              <p>📅 {new Date(selectedMemory.date_range_start).toLocaleDateString()}</p>
              {selectedMemory.location && <p>📍 {selectedMemory.location}</p>}
              <p>🖼️ {selectedMemory.image_count} photos</p>
            </div>
            <button
              onClick={() => setSelectedMemory(null)}
              className="mt-6 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Memories;
