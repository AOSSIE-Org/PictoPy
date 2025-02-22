import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { motion, AnimatePresence } from 'framer-motion';
import MediaView from '../Media/MediaView';
import PaginationControls from '../ui/PaginationControls';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Loader2, X } from 'lucide-react';
import { useLocalStorage } from '@/hooks/LocalStorage';

interface MemoryImage {
  path: string;
  created_at: string;
}

const Memories: React.FC = () => {
  const [memories, setMemories] = useState<MemoryImage[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [showMediaView, setShowMediaView] = useState(false);
  const [selectedMemoryIndex, setSelectedMemoryIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [showStoryView, setShowStoryView] = useState(false); // Default to false
  const [storyIndex, setStoryIndex] = useState(0);
  const itemsPerPage = 12;
  const [currentPath] = useLocalStorage('folderPath', '');
  const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  const storyDuration = 3000; // 3 seconds per story

  useEffect(() => {
    fetchMemories();
  }, [currentPath]);

  const fetchMemories = async () => {
    try {
      setIsLoading(true);
      const directories =
        currentPaths.length > 0 ? currentPaths : [currentPath];
      console.log(directories);
      const result = await invoke<MemoryImage[]>('get_random_memories', {
        directories,
        count: 10,
      });
      setMemories(result);
    } catch (error) {
      console.error('Failed to fetch memories:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (showStoryView && memories.length > 0) {
      const timer = setTimeout(() => {
        if (storyIndex < memories.length - 1) {
          setStoryIndex((prev) => prev + 1);
        } else {
          setShowStoryView(false);
        }
      }, storyDuration);

      return () => clearTimeout(timer);
    }
  }, [storyIndex, showStoryView, memories]);

  const currentMemories = useMemo(() => {
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    return memories.slice(indexOfFirstItem, indexOfLastItem);
  }, [memories, currentPage]);

  const totalPages = Math.ceil(memories.length / itemsPerPage);

  const openMediaView = useCallback((index: number) => {
    setSelectedMemoryIndex(index);
    setShowMediaView(true);
  }, []);

  const closeMediaView = useCallback(() => {
    setShowMediaView(false);
  }, []);

  // Function to get the time ago (e.g., "2 days ago", "1 month ago", etc.)
  const getTimeAgo = (dateStr: string) => {
    try {
      const timestamp = parseInt(dateStr) * 1000;
      const date = new Date(timestamp);
      const now = new Date();
      const diffTime = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      const diffMonths = Math.floor(diffDays / 30);
      const diffYears = Math.floor(diffDays / 365);

      if (diffYears > 0)
        return `${diffYears} year${diffYears > 1 ? 's' : ''} ago`;
      if (diffMonths > 0)
        return `${diffMonths} month${diffMonths > 1 ? 's' : ''} ago`;
      if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
      return 'Today';
    } catch (error) {
      console.error('Error parsing date:', error);
      return 'Recently';
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-lg text-muted-foreground">
            Loading your memories...
          </p>
        </div>
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="min-h-screen bg-background p-8">
        <h1 className="mb-8 text-center text-4xl font-bold">Your Memories</h1>
        <div className="flex items-center justify-center">
          <p className="text-lg text-muted-foreground">
            No memories found in the selected folder.
          </p>
        </div>
      </div>
    );
  }

  if (showStoryView && memories.length > 0) {
    const currentMemory = memories[storyIndex];
    return (
      <div className="fixed inset-0 bg-black">
        <button
          onClick={() => setShowStoryView(false)}
          className="absolute right-4 top-4 z-50 text-white hover:text-gray-300"
        >
          <X className="h-6 w-6" />
        </button>
        <AnimatePresence mode="wait">
          <motion.div
            key={storyIndex}
            initial={{ opacity: 0, scale: 1.1 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.5 }}
            className="relative flex h-full w-full items-center justify-center"
          >
            <img
              src={convertFileSrc(currentMemory.path)}
              alt={`Memory ${storyIndex + 1}`}
              className="h-full w-full object-contain"
            />
            <div className="absolute left-0 top-0 h-1 w-full bg-gray-800">
              <motion.div
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: storyDuration / 1000, ease: 'linear' }}
                className="h-full bg-white"
              />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <h1 className="mb-8 text-center text-4xl font-bold">Your Memories</h1>
      <AnimatePresence mode="wait">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
        >
          {currentMemories.map((memory, index) => (
            <motion.div
              key={memory.path}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="group relative cursor-pointer overflow-hidden rounded-lg bg-card shadow-lg"
              onClick={() => openMediaView(index)}
            >
              <div className="aspect-square overflow-hidden">
                <img
                  src={convertFileSrc(memory.path)}
                  alt={`Memory ${index + 1}`}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                />
              </div>
              {/* Show time ago under each memory */}
              <div className="rounded absolute bottom-2 left-2 bg-gray-800 bg-opacity-50 p-2 text-white">
                {getTimeAgo(memory.created_at)}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>

      {totalPages > 1 && (
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}

      {showMediaView && (
        <MediaView
          initialIndex={selectedMemoryIndex}
          onClose={closeMediaView}
          allMedia={memories.map((memory) => ({
            url: convertFileSrc(memory.path),
            path: memory.path,
          }))}
          currentPage={currentPage}
          itemsPerPage={itemsPerPage}
          type="image"
        />
      )}
    </div>
  );
};

export default Memories;
