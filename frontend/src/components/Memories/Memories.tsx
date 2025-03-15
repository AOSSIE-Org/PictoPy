import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { motion, AnimatePresence } from 'framer-motion';
import MediaView from '../Media/MediaView';
import PaginationControls from '../ui/PaginationControls';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Loader2, X, Clock } from 'lucide-react';
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
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-background to-background/80">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center gap-6 text-center"
        >
          <div className="relative">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <div className="rounded-full absolute inset-0 h-12 w-12 border-2 border-primary/20"></div>
          </div>
          <div>
            <p className="mb-1 text-xl font-semibold text-primary">
              Loading your memories...
            </p>
            <p className="text-sm text-muted-foreground">
              Please wait while we find your special moments
            </p>
          </div>
        </motion.div>
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-background/80 p-8">
        <h1 className="mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-center text-4xl font-bold text-transparent">
          Your Memories
        </h1>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center gap-6"
        >
          <div className="rounded-full bg-gray-100 p-8 dark:bg-gray-800">
            <Clock className="h-16 w-16 text-gray-400" />
          </div>
          <p className="max-w-md text-center text-xl text-muted-foreground">
            No memories found in the selected folder. Photos will appear here
            once you've added some images.
          </p>
        </motion.div>
      </div>
    );
  }

  if (showStoryView && memories.length > 0) {
    const currentMemory = memories[storyIndex];
    return (
      <div className="fixed inset-0 bg-black">
        <button
          onClick={() => setShowStoryView(false)}
          className="rounded-full absolute right-4 top-4 z-50 bg-black/40 p-2 text-white transition-all duration-300 hover:bg-black/60"
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
            <div className="absolute left-0 top-0 h-2 w-full bg-gray-800">
              <motion.div
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: storyDuration / 1000, ease: 'linear' }}
                className="h-full bg-gradient-to-r from-blue-500 to-purple-600"
              />
            </div>
            <div className="absolute bottom-10 left-0 right-0 text-center">
              <p className="rounded-full inline-block bg-black/60 px-4 py-2 text-sm text-white backdrop-blur-sm">
                {getTimeAgo(currentMemory.created_at)}
              </p>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-background/80 px-4 py-8 sm:px-8">
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-center text-4xl font-bold text-transparent"
      >
        Your Memories
      </motion.h1>

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
              className="rounded-xl group relative cursor-pointer overflow-hidden bg-card shadow-md transition-all duration-500 hover:shadow-xl hover:shadow-blue-900/5 dark:hover:shadow-blue-900/20"
              onClick={() => openMediaView(index)}
            >
              <div className="aspect-square overflow-hidden">
                <img
                  src={convertFileSrc(memory.path)}
                  alt={`Memory ${index + 1}`}
                  className="h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-110"
                />
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100"></div>
              {/* Show time ago under each memory */}
              <div className="absolute bottom-0 left-0 right-0 translate-y-full transform p-4 transition-transform duration-300 group-hover:translate-y-0">
                <div className="flex items-center gap-2 rounded-lg bg-black/70 px-3 py-2 text-white backdrop-blur-sm">
                  <Clock className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    {getTimeAgo(memory.created_at)}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>

      {totalPages > 1 && (
        <div className="mt-8">
          <PaginationControls
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
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
