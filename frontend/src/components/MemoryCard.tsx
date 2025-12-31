import React from 'react';
import { Memory } from '../types/memory';

interface MemoryCardProps {
  memory: Memory;
  onClick?: () => void;
}

export const MemoryCard: React.FC<MemoryCardProps> = ({ memory, onClick }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getMemoryIcon = (type: string) => {
    switch (type) {
      case 'on_this_day':
        return '📅';
      case 'location_trip':
        return '📍';
      default:
        return '🖼️';
    }
  };

  return (
    <div
      onClick={onClick}
      className="memory-card group relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 dark:from-gray-800 dark:to-gray-900 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:scale-105"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">{getMemoryIcon(memory.memory_type)}</span>
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {memory.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {formatDate(memory.date_range_start)}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400">
            <span>🖼️</span>
            <span>{memory.image_count}</span>
          </div>
        </div>

        {/* Description */}
        {memory.description && (
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 line-clamp-2">
            {memory.description}
          </p>
        )}

        {/* Location */}
        {memory.location && (
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
            <span>📍</span>
            <span className="truncate">{memory.location}</span>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {memory.memory_type === 'on_this_day' ? 'On This Day' : 'Trip Memory'}
          </span>
          <button className="text-sm text-purple-600 dark:text-purple-400 font-medium hover:underline">
            View →
          </button>
        </div>
      </div>

      {/* Decorative gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-transparent to-white/10 dark:to-black/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
    </div>
  );
};
