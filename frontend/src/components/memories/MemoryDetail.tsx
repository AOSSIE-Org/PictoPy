/**
 * Memory Detail Component
 * 
 * Full-screen modal view displaying all images in a memory with
 * story-style presentation.
 */

import React, { useState } from 'react';
import { Memory } from '../../types/memories';
import { X, Calendar, MapPin, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';

interface MemoryDetailProps {
  memory: Memory;
  onClose: () => void;
  onDelete: (memoryId: number) => void;
}

const MemoryDetail: React.FC<MemoryDetailProps> = ({ memory, onClose, onDelete }) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric', 
        year: 'numeric',
        weekday: 'long'
      });
    } catch {
      return dateStr;
    }
  };

  const handlePrevious = () => {
    setCurrentImageIndex((prev) => 
      prev === 0 ? memory.images.length - 1 : prev - 1
    );
  };

  const handleNext = () => {
    setCurrentImageIndex((prev) => 
      prev === memory.images.length - 1 ? 0 : prev + 1
    );
  };

  const handleDelete = () => {
    if (memory.id) {
      onDelete(memory.id);
    }
  };

  const currentImage = memory.images[currentImageIndex];

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] p-0">
        {/* Header */}
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="text-2xl mb-2">{memory.title}</DialogTitle>
              <p className="text-gray-600">{memory.description}</p>
              
              <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span>{formatDate(memory.start_date)}</span>
                </div>
                
                {memory.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    <span>{memory.location}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowDeleteConfirm(true)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        {/* Main Image Display */}
        <div className="flex-1 relative bg-black">
          {currentImage && (
            <img
              src={`file://${currentImage.path}`}
              alt={`Memory ${currentImageIndex + 1}`}
              className="w-full h-full object-contain"
            />
          )}

          {/* Navigation Buttons */}
          {memory.images.length > 1 && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white"
                onClick={handlePrevious}
              >
                <ChevronLeft className="w-6 h-6" />
              </Button>
              
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white"
                onClick={handleNext}
              >
                <ChevronRight className="w-6 h-6" />
              </Button>

              {/* Image Counter */}
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-full text-sm">
                {currentImageIndex + 1} / {memory.images.length}
              </div>
            </>
          )}
        </div>

        {/* Thumbnail Strip */}
        {memory.images.length > 1 && (
          <div className="px-6 py-4 border-t bg-gray-50">
            <div className="flex gap-2 overflow-x-auto">
              {memory.images.map((img, index) => (
                <button
                  key={img.id}
                  onClick={() => setCurrentImageIndex(index)}
                  className={`flex-shrink-0 w-20 h-20 rounded overflow-hidden border-2 transition-all ${
                    index === currentImageIndex
                      ? 'border-blue-500 scale-110'
                      : 'border-transparent opacity-60 hover:opacity-100'
                  }`}
                >
                  <img
                    src={`file://${img.path}`}
                    alt={`Thumbnail ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-sm">
              <h3 className="text-lg font-semibold mb-2">Delete Memory?</h3>
              <p className="text-gray-600 mb-4">
                This will remove the memory but won't delete the photos from your gallery.
              </p>
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                >
                  Delete Memory
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default MemoryDetail;
