/**
 * Memory Card Component
 * 
 * Displays a single memory as an interactive card with cover image,
 * title, description, and metadata.
 */

import React from 'react';
import { Memory } from '../../types/memories';
import { Calendar, MapPin, Images } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

interface MemoryCardProps {
  memory: Memory;
  onClick: () => void;
}

const MemoryCard: React.FC<MemoryCardProps> = ({ memory, onClick }) => {
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric', 
        year: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  const getMemoryIcon = () => {
    if (memory.type === 'time_based') {
      return <Calendar className="w-5 h-5 text-blue-500" />;
    } else {
      return <MapPin className="w-5 h-5 text-red-500" />;
    }
  };

  return (
    <Card 
      className="cursor-pointer hover:shadow-lg transition-all duration-300 overflow-hidden group"
      onClick={onClick}
    >
      {/* Cover Image */}
      <div className="relative h-48 overflow-hidden bg-gray-200">
        {memory.cover_image?.path ? (
          <img
            src={`file://${memory.cover_image.path}`}
            alt={memory.title}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
          />
        ) : (
          <div className="flex items-center justify-center h-full bg-gradient-to-br from-purple-400 to-pink-400">
            <Images className="w-16 h-16 text-white opacity-50" />
          </div>
        )}
        
        {/* Memory Type Badge */}
        <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full flex items-center gap-2">
          {getMemoryIcon()}
          <span className="text-xs font-medium">
            {memory.image_count} {memory.image_count === 1 ? 'photo' : 'photos'}
          </span>
        </div>
      </div>

      <CardHeader>
        <CardTitle className="text-lg line-clamp-2">
          {memory.title}
        </CardTitle>
        <CardDescription className="line-clamp-2">
          {memory.description}
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="space-y-2 text-sm text-gray-600">
          {/* Date Range */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(memory.start_date)}</span>
          </div>

          {/* Location */}
          {memory.location && (
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              <span className="truncate">{memory.location}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default MemoryCard;
