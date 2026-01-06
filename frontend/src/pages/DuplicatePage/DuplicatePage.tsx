import React, { useEffect, useState } from 'react';
import { duplicatesEndpoints } from '@/api/apiEndpoints';
import { apiClient as axiosInstance } from '@/api/axiosConfig';
import { convertFileSrc } from '@tauri-apps/api/core';
import { ask } from '@tauri-apps/plugin-dialog';
import { Trash2, CheckCircle, X, ZoomIn, ChevronLeft, ChevronRight } from 'lucide-react';

interface Image {
  id: string;
  path: string;
  thumbnailPath: string;
  phash: string;
}

interface DuplicateGroup {
  images: Image[];
  best_shot_id: string | null;
}

export const DuplicatePage: React.FC = () => {
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [viewingImage, setViewingImage] = useState<Image | null>(null);

  useEffect(() => {
    fetchDuplicates();
  }, []);

  const fetchDuplicates = async () => {
    try {
      const response = await axiosInstance.get(duplicatesEndpoints.getDuplicates);
      setGroups(response.data);
      
      // Pre-select duplicates (all except best shot)
      const initialSelection = new Set<string>();
      response.data.forEach((group: DuplicateGroup) => {
        group.images.forEach((img) => {
          if (img.id !== group.best_shot_id) {
            initialSelection.add(img.id);
          }
        });
      });
      setSelectedIds(initialSelection);
    } catch (error) {
      console.error('Error fetching duplicates:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelection = (id: string) => {
    const newSelection = new Set(selectedIds);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedIds(newSelection);
  };

  const handleDelete = async () => {
    if (selectedIds.size === 0) return;
    const confirmed = await ask(`Are you sure you want to delete ${selectedIds.size} images?`, {
      title: 'Confirm Deletion',
      kind: 'warning',
    });

    if (!confirmed) return;

    try {
      await axiosInstance.post(duplicatesEndpoints.deleteDuplicates, Array.from(selectedIds));
      // Refresh
      fetchDuplicates();
    } catch (error) {
      console.error('Error deleting duplicates:', error);
    }
  };

  const navigateImage = (direction: 'prev' | 'next') => {
    if (!viewingImage) return;
    for (const group of groups) {
      const idx = group.images.findIndex(img => img.id === viewingImage.id);
      if (idx !== -1) {
        let newIdx;
        if (direction === 'prev') {
          newIdx = idx === 0 ? group.images.length - 1 : idx - 1;
        } else {
          newIdx = (idx + 1) % group.images.length;
        }
        setViewingImage(group.images[newIdx]);
        return;
      }
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!viewingImage) return;
      
      switch (e.key) {
        case 'ArrowLeft':
          navigateImage('prev');
          break;
        case 'ArrowRight':
          navigateImage('next');
          break;
        case 'Escape':
          setViewingImage(null);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [viewingImage, groups]);

  const handlePrev = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigateImage('prev');
  };

  const handleNext = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigateImage('next');
  };

  if (loading) return <div className="p-8 text-center">Loading duplicates...</div>;

  if (groups.length === 0) {
    return (
      <div className="p-8 text-center">
        <h2 className="text-2xl font-bold mb-4">No Duplicates Found</h2>
        <p>Great! Your gallery seems to be free of duplicate photos.</p>
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Duplicate Photos</h1>
        <button
          onClick={handleDelete}
          disabled={selectedIds.size === 0}
          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded flex items-center gap-2 disabled:opacity-50"
        >
          <Trash2 size={18} />
          Delete Selected ({selectedIds.size})
        </button>
      </div>

      <div className="space-y-8">
        {groups.map((group, index) => (
          <div key={index} className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
            <div className="mb-2 text-sm text-gray-400">
              Group {index + 1} • {group.images.length} images
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {group.images.map((img) => {
                const isBest = img.id === group.best_shot_id;
                const isSelected = selectedIds.has(img.id);
                
                return (
                  <div 
                    key={img.id} 
                    className={`relative group rounded-lg overflow-hidden border-2 ${
                      isBest ? 'border-green-500' : isSelected ? 'border-red-500' : 'border-transparent'
                    }`}
                  >
                    <div 
                      className="cursor-zoom-in relative"
                      onClick={() => setViewingImage(img)}
                    >
                      <img
                        src={convertFileSrc(img.thumbnailPath)}
                        alt="Duplicate"
                        className="w-full h-48 object-cover transition-transform hover:scale-105"
                      />
                      <div className="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 hover:opacity-100">
                        <ZoomIn className="text-white drop-shadow-md" size={24} />
                      </div>
                    </div>
                    
                    {isBest && (
                      <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                        <CheckCircle size={12} /> Best Shot
                      </div>
                    )}

                    <div className="absolute top-2 right-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelection(img.id)}
                        className="w-5 h-5 rounded border-gray-300 text-red-600 focus:ring-red-500"
                      />
                    </div>
                    
                    <div className="absolute bottom-0 left-0 right-0 bg-black/60 p-2 text-xs text-white truncate">
                      {img.path.split('/').pop()}
                    </div>
                  </div>
                );
              })}
            </div>

      {/* Image Preview Modal */}
      {viewingImage && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 p-4 animate-in fade-in duration-200"
          onClick={() => setViewingImage(null)}
        >
          <div className="relative max-w-[95vw] max-h-[95vh] flex flex-col items-center justify-center" onClick={(e) => e.stopPropagation()}>
             <div className="absolute top-2 left-2 z-50 bg-black/60 text-white px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm shadow-lg pointer-events-none">
                {(() => {
                  const group = groups.find(g => g.images.some(i => i.id === viewingImage.id));
                  if (!group) return '';
                  const index = group.images.findIndex(i => i.id === viewingImage.id) + 1;
                  return `${index} / ${group.images.length}`;
                })()}
             </div>

             {/* Navigation Buttons */}
             <button 
                className="absolute left-2 md:-left-16 top-1/2 -translate-y-1/2 text-white hover:text-gray-300 transition-colors bg-white/10 hover:bg-white/20 p-2 rounded-full z-10"
                onClick={handlePrev}
                title="Previous Image"
             >
                <ChevronLeft size={32} />
             </button>

             <img 
                src={convertFileSrc(viewingImage.path)} 
                className="max-w-full max-h-[85vh] object-contain rounded-md shadow-2xl" 
                alt="Preview"
             />
             
             <div className="mt-4 text-white text-center bg-black/60 px-4 py-2 rounded-full backdrop-blur-sm">
                <p className="font-medium truncate max-w-2xl">{viewingImage.path.split('/').pop()}</p>
                <p className="text-xs text-gray-300 truncate max-w-2xl">{viewingImage.path}</p>
             </div>

             <button 
                className="absolute right-2 md:-right-16 top-1/2 -translate-y-1/2 text-white hover:text-gray-300 transition-colors bg-white/10 hover:bg-white/20 p-2 rounded-full z-10"
                onClick={handleNext}
                title="Next Image"
             >
                <ChevronRight size={32} />
             </button>

             <button 
                className="absolute -top-12 right-0 md:-right-12 md:-top-0 text-white hover:text-gray-300 transition-colors bg-white/10 hover:bg-white/20 p-2 rounded-full"
                onClick={() => setViewingImage(null)}
             >
                <X size={32} />
             </button>
          </div>
        </div>
      )}
          </div>
        ))}
      </div>
    </div>
  );
};
