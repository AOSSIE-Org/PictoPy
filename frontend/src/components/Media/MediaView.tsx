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

const MediaView: React.FC<MediaViewProps> = ({
  initialIndex,
  onClose,
  allMedia,
  currentPage,
  itemsPerPage,
  type,
}) => {
  const [globalIndex, setGlobalIndex] = useState<number>(
    (currentPage - 1) * itemsPerPage + initialIndex,
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

  useEffect(() => {
    setGlobalIndex((currentPage - 1) * itemsPerPage + initialIndex);
  }, [initialIndex, currentPage, itemsPerPage]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowRight') {
        handleNextItem();
      } else if (e.key === 'ArrowLeft') {
        handlePrevItem();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [globalIndex, onClose]);

  const handelZoomOut = () => {
    setScale((s) => Math.max(0.1, s - 0.1));
  };
  const handelZoomIn = () => {
    setScale((s) => Math.min(4, s + 0.1));
  };

  const handleWheel = (e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY * -0.01;
    const newScale = Math.min(Math.max(0.1, scale + delta), 4);
    setScale(newScale);
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

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetZoom = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
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

      <div
        className="relative z-50 flex h-full w-full items-center justify-center"
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            onClose();
          }
        }}
      >
        <button
          onClick={onClose}
          className="absolute left-4 top-4 z-50 rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
        >
          Back
        </button>

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
            className="relative flex h-full w-full items-center justify-center overflow-hidden align-middle"
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
            </div>
          </div>
        ) : (
          <video
            src={allMedia[globalIndex].url}
            className="max-h-full"
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
