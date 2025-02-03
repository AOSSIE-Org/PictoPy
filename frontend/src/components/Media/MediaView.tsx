import React, { useEffect, useState, useCallback } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Edit,
  Share2,
  Check,
  X,
  SunMoon,
  Contrast,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Heart,
  Play,
  Pause,
  Lock,
} from 'lucide-react';
import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { invoke } from '@tauri-apps/api/core';
import { readFile } from '@tauri-apps/plugin-fs';
import { useNavigate } from 'react-router-dom';

interface MediaViewProps {
  initialIndex: number;
  onClose: () => void;
  allMedia: { url: string; path?: string }[];
  currentPage: number;
  itemsPerPage: number;
  type: 'image' | 'video';
  isSecureFolder?: boolean;
}

const MediaView: React.FC<MediaViewProps> = ({
  initialIndex,
  onClose,
  allMedia,
  currentPage,
  itemsPerPage,
  type,
  isSecureFolder = false,
}) => {
  const [globalIndex, setGlobalIndex] = useState<number>(
    (currentPage - 1) * itemsPerPage + initialIndex
  );
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isSlideshowActive, setIsSlideshowActive] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [favorites, setFavorites] = useState<string[]>(() => {
    const saved = localStorage.getItem('pictopy-favorites');
    return saved ? JSON.parse(saved) : [];
  });
  const [crop, setCrop] = useState<Crop | undefined>(undefined);
  const [completedCrop, setCompletedCrop] = useState<Crop | undefined>(undefined);
  const [filter, setFilter] = useState('');
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setGlobalIndex((currentPage - 1) * itemsPerPage + initialIndex);
  }, [initialIndex, currentPage, itemsPerPage]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') handleNextItem();
      if (e.key === 'ArrowLeft') handlePrevItem();
      if (e.key === '+') handleZoomIn();
      if (e.key === '-') handleZoomOut();
      if (e.key === 'r') handleRotate();
      if (e.key === 'f') toggleFavorite();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [globalIndex, onClose, favorites]);

  useEffect(() => {
    let slideshowInterval: NodeJS.Timeout | null = null;

    if (isSlideshowActive) {
      slideshowInterval = setInterval(() => {
        handleNextItem();
      }, 3000);
    }

    return () => {
      if (slideshowInterval) clearInterval(slideshowInterval);
    };
  }, [isSlideshowActive, globalIndex]);

  const handleZoomIn = () => setScale((s) => Math.min(4, s + 0.1));
  const handleZoomOut = () => setScale((s) => Math.max(0.5, s - 0.1));
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360);

  const toggleFavorite = () => {
    const currentMedia = allMedia[globalIndex];
    setFavorites((prev) => {
      const newFavorites = prev.includes(currentMedia.url)
        ? prev.filter((f) => f !== currentMedia.url)
        : [...prev, currentMedia.url];

      localStorage.setItem('pictopy-favorites', JSON.stringify(newFavorites));
      return newFavorites;
    });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetZoom = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
    setRotation(0);
  };

  const resetEditing = () => {
    setIsEditing(false);
    setFilter('');
    setBrightness(100);
    setContrast(100);
    setCrop(undefined);
    setCompletedCrop(undefined);
  };

  const handlePrevItem = () => {
    setGlobalIndex(globalIndex > 0 ? globalIndex - 1 : allMedia.length - 1);
    resetZoom();
  };

  const handleNextItem = () => {
    setGlobalIndex(globalIndex < allMedia.length - 1 ? globalIndex + 1 : 0);
    resetZoom();
  };

  const toggleSlideshow = () => {
    setIsSlideshowActive((prev) => !prev);
  };

  const isFavorite = (mediaUrl: string) => favorites.includes(mediaUrl);

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: `Shared Media ${globalIndex + 1}`,
          url: allMedia[globalIndex].url,
        });
      } else {
        await navigator.clipboard.writeText(allMedia[globalIndex].url);
        console.log('Link copied to clipboard!');
      }
    } catch (error) {
      console.error('Share failed:', error);
    }
  };

  const handleThumbnailClick = (index: number) => {
    setGlobalIndex(index);
    resetZoom();
  };

  const handleEditComplete = async () => {
    // Placeholder for editing logic
    console.log('Edit saved');
    setIsEditing(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black">
      <div className="absolute right-4 top-4 z-50 flex items-center gap-2">
        <button
          onClick={handleShare}
          className="rounded-full bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
          aria-label="Share"
        >
          <Share2 className="h-6 w-6" />
        </button>
        {type === 'image' && (
          <button
            onClick={() => setIsEditing(true)}
            className="rounded-full bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
            aria-label="Edit"
          >
            <Edit className="h-6 w-6" />
          </button>
        )}
        {type === 'image' && (
          <button
            onClick={toggleSlideshow}
            className="flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-white transition-colors duration-200 hover:bg-white/40"
            aria-label="Toggle Slideshow"
          >
            {isSlideshowActive ? (
              <Pause className="h-5 w-5" />
            ) : (
              <Play className="h-5 w-5" />
            )}
            {isSlideshowActive ? 'Pause' : 'Slideshow'}
          </button>
        )}
        <button
          onClick={onClose}
          className="rounded-full bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
          aria-label="Close"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      <div className="relative flex h-full w-full items-center justify-center">
        {type === 'image' ? (
          <img
            src={allMedia[globalIndex].url}
            alt={`media-${globalIndex}`}
            draggable={false}
            className="h-full w-full object-contain"
            style={{
              transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
              cursor: isDragging ? 'grabbing' : 'grab',
              filter: `${filter} brightness(${brightness}%) contrast(${contrast}%)`,
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
        ) : (
          <video
            src={allMedia[globalIndex].url}
            controls
            autoPlay
            className="h-full w-full object-contain"
          />
        )}

        <button
          onClick={handlePrevItem}
          className="absolute left-4 top-1/2 z-50 flex items-center rounded-full bg-white/20 p-3 text-white transition-colors duration-200 hover:bg-white/40"
        >
          <ChevronLeft className="h-6 w-6" />
        </button>
        <button
          onClick={handleNextItem}
          className="absolute right-4 top-1/2 z-50 flex items-center rounded-full bg-white/20 p-3 text-white transition-colors duration-200 hover:bg-white/40"
        >
          <ChevronRight className="h-6 w-6" />
        </button>
      </div>

      {type === 'image' && (
        <div className="absolute bottom-20 right-4 flex gap-2">
          <button
            onClick={handleZoomOut}
            className="rounded-md bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
            aria-label="Zoom Out"
          >
            <ZoomOut className="h-5 w-5" />
          </button>
          <button
            onClick={resetZoom}
            className="rounded-md bg-white/20 px-4 py-2 text-white transition-colors duration-200 hover:bg-white/40"
          >
            Reset
          </button>
          <button
            onClick={handleZoomIn}
            className="rounded-md bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
            aria-label="Zoom In"
          >
            <ZoomIn className="h-5 w-5" />
          </button>
          <button
            onClick={handleRotate}
            className="rounded-md bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
            aria-label="Rotate"
          >
            <RotateCw className="h-5 w-5" />
          </button>
          {isEditing && (
            <>
              <button
                onClick={handleEditComplete}
                className="rounded-md bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
                aria-label="Confirm Edit"
              >
                <Check className="h-5 w-5" />
              </button>
              <button
                onClick={resetEditing}
                className="rounded-md bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
                aria-label="Cancel Edit"
              >
                <X className="h-5 w-5" />
              </button>
              <select
                onChange={(e) => setFilter(e.target.value)}
                className="rounded-md bg-white/20 px-2 py-2 text-white"
              >
                <option value="">No Filter</option>
                <option value="grayscale(100%)">Grayscale</option>
                <option value="sepia(100%)">Sepia</option>
                <option value="invert(100%)">Invert</option>
              </select>
              <div className="flex items-center gap-2">
                <SunMoon className="h-5 w-5 text-white" />
                <input
                  type="range"
                  min="0"
                  max="200"
                  value={brightness}
                  onChange={(e) => setBrightness(Number(e.target.value))}
                  className="w-24"
                />
              </div>
              <div className="flex items-center gap-2">
                <Contrast className="h-5 w-5 text-white" />
                <input
                  type="range"
                  min="0"
                  max="200"
                  value={contrast}
                  onChange={(e) => setContrast(Number(e.target.value))}
                  className="w-24"
                />
              </div>
            </>
          )}
        </div>
      )}

      <div className="absolute bottom-0 flex w-full items-center justify-center gap-2 overflow-x-auto bg-black/50 px-4 py-2">
        {allMedia.map((media, index) => (
          <div
            key={index}
            onClick={() => handleThumbnailClick(index)}
            className={`relative h-16 w-24 flex-shrink-0 overflow-hidden rounded-lg border-2 ${
              index === globalIndex
                ? 'border-blue-500 shadow-lg'
                : 'border-transparent'
            }`}
          >
            {isFavorite(media.url) && (
              <Heart className="absolute right-1 top-1 h-4 w-4 fill-current text-red-500" />
            )}
            <img
              src={media.url}
              alt={`thumbnail-${index}`}
              className="h-full w-full object-cover"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default MediaView;