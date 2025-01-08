import { MediaViewProps } from '@/types/Media';
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
} from 'lucide-react';
import ReactCrop, { Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { invoke } from '@tauri-apps/api/core';
import { readFile } from '@tauri-apps/plugin-fs';

import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, X, Play, Pause, RotateCw, Heart, Share2, ZoomIn, ZoomOut } from 'lucide-react';

interface MediaViewProps {
  initialIndex: number;
  onClose: () => void;
  allMedia: string[];
  currentPage: number;
  itemsPerPage: number;
  type: 'image' | 'video';
}

const MediaView: React.FC<MediaViewProps> = ({
  initialIndex,
  onClose,
  allMedia,
  currentPage,
  itemsPerPage,
  type,
}) => {
  // State management
  const [globalIndex, setGlobalIndex] = useState<number>(
    (currentPage - 1) * itemsPerPage + initialIndex
  );
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isEditing, setIsEditing] = useState(false);
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<Crop>();
  const [filter, setFilter] = useState('');
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [notification, setNotification] = useState<{
    message: string;
    type: 'success' | 'error';
  } | null>(null);
  const [isSlideshowActive, setIsSlideshowActive] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [favorites, setFavorites] = useState<string[]>(() => {
    const saved = localStorage.getItem('pictopy-favorites');
    return saved ? JSON.parse(saved) : [];
  });

  
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
    setFavorites(prev => {
      const newFavorites = prev.includes(currentMedia)
        ? prev.filter(f => f !== currentMedia)
        : [...prev, currentMedia];
      
      localStorage.setItem('pictopy-favorites', JSON.stringify(newFavorites));
      return newFavorites;
    });
  };

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: `Shared Image ${globalIndex + 1}`,
          url: allMedia[globalIndex]
        });
      } else {
        await navigator.clipboard.writeText(allMedia[globalIndex]);
        console.log('Link copied to clipboard!');
      }
    } catch (error) {
      console.error('Share failed:', error);
    }
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

  useEffect(() => {
    const element = document.getElementById('zoomable-image');
    element?.addEventListener('wheel', handleWheel, { passive: false });
    return () => element?.removeEventListener('wheel', handleWheel);
  }, [scale]);

  function handlePrevItem() {
    if (globalIndex > 0) {
      setGlobalIndex(globalIndex - 1);
    } else {
      setGlobalIndex(allMedia.length - 1);
    }
    resetZoom();
    resetEditing();
  }

  function handleNextItem() {
    if (globalIndex < allMedia.length - 1) {
      setGlobalIndex(globalIndex + 1);
    } else {
      setGlobalIndex(0);
    }
    resetZoom();
    resetEditing();
  }

  const resetEditing = () => {
    setIsEditing(false);
    setCrop(undefined);
    setCompletedCrop(undefined);
    setFilter('');
    setBrightness(100);
    setContrast(100);
    setPosition({ x: 0, y: 0 });
    setScale(1);
  };

  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
    console.log(`Notification: ${type} - ${message}`); // Add console logging for debugging
  };

  const handleShare = async () => {
    try {
      const filePath = allMedia[globalIndex].path;
      await invoke('share_file', { path: filePath });
      showNotification('File shared successfully', 'success');
    } catch (err: any) {
      showNotification(`Failed to share: ${err}`, 'error');
    }
  };

  const handleEditComplete = useCallback(async () => {
    console.log('Starting handleEditComplete');

    try {
      // Read the image file using Tauri's filesystem API
      const imageData = await readFile(allMedia[globalIndex].path || '');
      console.log('Image file read successfully');

      // Create a Blob from the file data
      const blob = new Blob([imageData], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);

      // Create an image element to load the file
      const img = new Image();
      img.src = imageUrl;
      await new Promise((resolve) => {
        img.onload = resolve;
      });

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      if (!ctx) {
        throw new Error('Unable to create image context');
      }

      if (completedCrop) {
        canvas.width = completedCrop.width;
        canvas.height = completedCrop.height;
        ctx.drawImage(
          img,
          completedCrop.x,
          completedCrop.y,
          completedCrop.width,
          completedCrop.height,
          0,
          0,
          completedCrop.width,
          completedCrop.height,
        );
      } else {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
      }

      ctx.filter = `${filter} brightness(${brightness}%) contrast(${contrast}%)`;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      console.log('Canvas prepared, attempting to create blob');

      const editedBlob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob(resolve, 'image/png');
      });

      if (!editedBlob) {
        throw new Error('Failed to create edited image blob');
      }

      console.log('Edited blob created successfully');

      const arrayBuffer = await editedBlob.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);

      console.log('Invoking save_edited_image');
      await invoke('save_edited_image', {
        imageData: Array.from(uint8Array),
        originalPath: allMedia[globalIndex].path,
        filter,
        brightness,
        contrast,
      });

      console.log('Image saved successfully');
      showNotification('Image saved successfully', 'success');

      // Clean up the object URL
      URL.revokeObjectURL(imageUrl);
    } catch (error) {
      console.error('Error in handleEditComplete:', error);
      showNotification(`Failed to save edited image: ${error}`, 'error');
    }

    setIsEditing(false);
  }, [
    completedCrop,
    filter,
    brightness,
    contrast,
    allMedia,
    globalIndex,
    showNotification,
  ]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black bg-opacity-90" />
  const handlePrevItem = () => {
    setGlobalIndex(globalIndex > 0 ? globalIndex - 1 : allMedia.length - 1);
    resetZoom();
  };

  const handleNextItem = () => {
    setGlobalIndex(globalIndex < allMedia.length - 1 ? globalIndex + 1 : 0);
    resetZoom();
  };

  const handleThumbnailClick = (index: number) => {
    setGlobalIndex(index);
    resetZoom();
  };

  const toggleSlideshow = () => {
    setIsSlideshowActive(prev => !prev);
  };

  const isFavorite = (mediaUrl: string) => favorites.includes(mediaUrl);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black">
      
      <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
        <button
          onClick={handleShare}
          className="rounded-full bg-white/20 p-2 text-white hover:bg-white/40 transition-colors duration-200"
          aria-label="Share"
        >
          <Share2 className="h-6 w-6" />
        </button>
        <button
          onClick={toggleFavorite}
          className={`rounded-full p-2 text-white transition-colors duration-300 ${
            isFavorite(allMedia[globalIndex])
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-white/20 hover:bg-white/40'
          }`}
          aria-label={isFavorite(allMedia[globalIndex]) ? 'Remove from favorites' : 'Add to favorites'}
        >
          <Heart
            className={`h-6 w-6 ${
              isFavorite(allMedia[globalIndex]) ? 'fill-current' : ''
            }`}
          />
        </button>
        <button
          onClick={toggleSlideshow}
          className="flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-white hover:bg-white/40 transition-colors duration-200"
          aria-label="Toggle Slideshow"
        >
          {isSlideshowActive ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
          {isSlideshowActive ? 'Pause' : 'Slideshow'}
        </button>
        <button
          onClick={onClose}
          className="rounded-full bg-white/20 p-2 text-white hover:bg-white/40 transition-colors duration-200"
          aria-label="Close"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      
      <div
        className="relative flex h-full w-full items-center justify-center"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        {type === 'image' ? (
          <div
            id="zoomable-image"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                onClose();
              }
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className="relative h-full w-full flex items-center justify-center overflow-hidden"
          >
            {isEditing ? (
              <ReactCrop
                crop={crop}
                onChange={(c) => setCrop(c)}
                onComplete={(c) => setCompletedCrop(c)}
              >
                <img
                  id="source-image"
                  src={allMedia[globalIndex].url}
                  alt={`image-${globalIndex}`}
                  style={{
                    filter: `${filter} brightness(${brightness}%) contrast(${contrast}%)`,
                  }}
                />
              </ReactCrop>
            ) : (
              <img
                src={allMedia[globalIndex].url}
                alt={`image-${globalIndex}`}
                draggable={false}
                className="max-h-full select-none"
                style={{
                  transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                  transition: isDragging ? 'none' : 'transform 0.1s',
                  cursor: isDragging ? 'grabbing' : 'grab',
                }}
              />
            )}
            <div className="absolute bottom-4 right-4 flex gap-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleEditComplete}
                    className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                  <button
                    onClick={resetEditing}
                    className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <select
                    onChange={(e) => setFilter(e.target.value)}
                    className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black"
                  >
                    <option value="">No Filter</option>
                    <option value="grayscale(100%)">Grayscale</option>
                    <option value="sepia(100%)">Sepia</option>
                    <option value="invert(100%)">Invert</option>
                  </select>
                  <div className="flex items-center gap-2">
                    <SunMoon />
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
                    <Contrast />
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
              ) : (
                <>
                  <button
                    onClick={handelZoomOut}
                    className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
                  >
                    -
                  </button>
                  <button
                    onClick={resetZoom}
                    className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
                  >
                    Reset
                  </button>
                  <button
                    onClick={handelZoomIn}
                    className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
                  >
                    +
                  </button>
                  {allMedia[globalIndex]?.path && (
                    <>
                      <button
                        onClick={() => setIsEditing(true)}
                        className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={handleShare}
                        className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
                      >
                        <Share2 className="h-4 w-4" />
                      </button>
                    </>
                  )}
                </>
              )}
            <img
              src={allMedia[globalIndex].url}
              alt={`media-${globalIndex}`}
              draggable={false}
              className="h-full w-full object-contain"
              style={{
                transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
                cursor: isDragging ? 'grabbing' : 'grab',
                transition: isDragging ? 'none' : 'transform 0.2s ease-in-out',
              }}
            />

            
            <div className="absolute bottom-20 right-4 flex gap-2">
              <button
                onClick={handleZoomOut}
                className="rounded-md bg-white/20 p-2 text-white hover:bg-white/40 transition-colors duration-200"
                aria-label="Zoom Out"
              >
                <ZoomOut className="h-5 w-5" />
              </button>
              <button
                onClick={resetZoom}
                className="rounded-md bg-white/20 px-4 py-2 text-white hover:bg-white/40 transition-colors duration-200"
              >
                Reset
              </button>
              <button
                onClick={handleZoomIn}
                className="rounded-md bg-white/20 p-2 text-white hover:bg-white/40 transition-colors duration-200"
                aria-label="Zoom In"
              >
                <ZoomIn className="h-5 w-5" />
              </button>
              <button
                onClick={handleRotate}
                className="rounded-md bg-white/20 p-2 text-white hover:bg-white/40 transition-colors duration-200"
                aria-label="Rotate"
              >
                <RotateCw className="h-5 w-5" />
              </button>
            </div>
          </div>
        ) : (
          <video
            src={allMedia[globalIndex].url}
            className="max-h-full"
            className="h-full w-full object-contain"
            controls
            autoPlay
          />
        )}

        <button
          onClick={handlePrevItem}
          className="absolute left-4 top-1/2 z-50 flex items-center rounded-[50%] border border-black bg-white p-2 text-black transition duration-100 hover:bg-slate-800 hover:text-white"
        >
          <ChevronLeft className="h-6 w-4" />
        </button>
        <button
          onClick={handleNextItem}
          className="absolute right-4 top-1/2 z-50 flex items-center rounded-[50%] border border-black bg-white p-2 text-black transition duration-100 hover:bg-slate-800 hover:text-white"
        >
          <ChevronRight className="h-6 w-4" />
        </button>        
        <button
          onClick={handlePrevItem}
          className="absolute left-4 top-1/2 z-50 flex items-center rounded-full bg-white/20 p-3 text-white hover:bg-white/40 transition-colors duration-200"
        >
          <ChevronLeft className="h-6 w-6" />
        </button>
        <button
          onClick={handleNextItem}
          className="absolute right-4 top-1/2 z-50 flex items-center rounded-full bg-white/20 p-3 text-white hover:bg-white/40 transition-colors duration-200"
        >
          <ChevronRight className="h-6 w-6" />
        </button>
      </div>

      {/* Thumbnails */}
      <div className="absolute bottom-0 flex w-full items-center justify-center gap-2 overflow-x-auto bg-black/50 px-4 py-2 opacity-0 transition-opacity duration-300 hover:opacity-100">
        {allMedia.map((media, index) => (
          <div
            key={index}
            onClick={() => handleThumbnailClick(index)}
            className={`relative h-16 w-24 flex-shrink-0 overflow-hidden rounded-lg border-2 ${
              index === globalIndex
                ? 'border-blue-500 shadow-lg'
                : 'border-transparent'
            } cursor-pointer transition-transform hover:scale-105`}
          >
            {isFavorite(media) && (
              <div className="absolute top-1 right-1 z-10">
                <Heart className="h-4 w-4 text-red-500 fill-current" />
              </div>
            )}
            {type === 'image' ? (
              <img
                src={media.url}
                alt={`thumbnail-${index}`}
                className="h-full w-full object-cover"
              />
            ) : (
              <video
                src={media.url}
                className="h-full w-full object-cover"
                muted
                playsInline
              />
            )}
          </div>
        ))}
      </div>
      {notification && (
        <div
          className={`fixed left-1/2 top-4 -translate-x-1/2 transform rounded-md p-4 ${
            notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'
          } z-50 text-lg font-bold text-white shadow-lg`}
        >
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default MediaView;
