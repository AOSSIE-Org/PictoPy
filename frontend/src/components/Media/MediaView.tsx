'use client';

import type { MediaViewProps } from '@/types/Media';
import type React from 'react';
import { useEffect, useState, useCallback } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Edit,
  Share2,
  Check,
  X,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Heart,
  Play,
  Pause,
  Lock,
  Info,
  ImageIcon,
  Folder,
  ExternalLink,
  Sliders,
  Instagram,
} from 'lucide-react';
import { Crops } from '../ui/Icons/Icons';
import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { invoke } from '@tauri-apps/api/core';
import { readFile } from '@tauri-apps/plugin-fs';
import { useNavigate } from 'react-router';
import NetflixStylePlayer from '../VideoPlayer/NetflixStylePlayer';
import { save } from '@tauri-apps/plugin-dialog';
import { ROUTES } from '@/constants/routes';

const MediaView: React.FC<MediaViewProps> = ({
  initialIndex,
  onClose,
  allMedia,
  currentPage,
  itemsPerPage,
  type,
  isSecureFolder,
}) => {
  // State management
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
  const [aspect, setaspect] = useState<number | undefined>(undefined);
  const [onaspect, setonaspect] = useState(false);
  const [filter, setFilter] = useState('');
  const [brightness, setBrightness] = useState(0);
  const [contrast, setContrast] = useState(0);
  const [vibrance, setVibrance] = useState(0);
  const [exposure, setExposure] = useState(0);
  const [temperature, setTemperature] = useState(0);
  const [sharpness, setSharpness] = useState(0);
  const [vignette, setVignette] = useState(0);
  const [highlights, setHighlights] = useState(0);
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
  const [showInfo, setShowInfo] = useState(false);
  const [showAdjustMenu, setShowAdjustMenu] = useState(false);
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
  }, [onClose]);

  useEffect(() => {
    let slideshowInterval: NodeJS.Timeout | null = null;

    if (isSlideshowActive) {
      slideshowInterval = setInterval(() => {
        setGlobalIndex((prevIndex) => (prevIndex + 1) % allMedia.length);
      }, 3000);
    }

    return () => {
      if (slideshowInterval) clearInterval(slideshowInterval);
    };
  }, [isSlideshowActive, allMedia.length]);

  const handleZoomIn = () => setScale((s) => Math.min(4, s + 0.1));
  const handleZoomOut = () => setScale((s) => Math.max(0.5, s - 0.1));
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360);

  const toggleFavorite = () => {
    const currentMedia = allMedia[globalIndex].path || '';
    setFavorites((prev) => {
      const newFavorites = prev.includes(currentMedia)
        ? prev.filter((f) => f !== currentMedia)
        : [...prev, currentMedia];

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

  const handlePrevItem = () => {
    setGlobalIndex(globalIndex > 0 ? globalIndex - 1 : allMedia.length - 1);
    resetZoom();
    resetEditing();
  };

  const handleNextItem = () => {
    setGlobalIndex(globalIndex < allMedia.length - 1 ? globalIndex + 1 : 0);
    resetZoom();
    resetEditing();
  };

  const resetEditing = () => {
    setIsEditing(false);
    setCrop(undefined);
    setCompletedCrop(undefined);
    setFilter('');
    setBrightness(0);
    setContrast(0);
    setVibrance(0);
    setExposure(0);
    setTemperature(0);
    setSharpness(0);
    setVignette(0);
    setHighlights(0);
    setPosition({ x: 0, y: 0 });
    setScale(1);
  };

  const showNotification = useCallback(
    (message: string, type: 'success' | 'error') => {
      setNotification({ message, type });
      setTimeout(() => setNotification(null), 5000);
      console.log(`Notification: ${type} - ${message}`);
    },
    [],
  );

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
      const imageData = await readFile(allMedia[globalIndex].path || '');
      console.log('Image file read successfully');

      const blob = new Blob([imageData], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);

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

      if (isSecureFolder) {
        // Save the edited image to a temporary location
        const tempPath = await invoke<string>('save_temp_image', {
          imageData: Array.from(uint8Array),
          originalPath: allMedia[globalIndex].path,
        });

        // Move the temporary file to the secure folder
        await invoke('move_to_secure_folder', {
          path: tempPath,
          password: prompt('Enter your secure folder password:'),
        });
      } else {
        const selectedPath = await save({
          defaultPath: `${allMedia[globalIndex].path?.replace(/\.\w+$/, '_edited.png')}`,
          filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg'] }],
        });

        if (!selectedPath) {
          console.log('User cancelled save dialog');
          return;
        }

        await invoke('save_edited_image', {
          imageData: Array.from(uint8Array),
          savePath: selectedPath,
          filter,
          brightness,
          contrast,
          vibrance,
          exposure,
          temperature,
          sharpness,
          vignette,
          highlights,
        });
      }

      console.log('Image saved successfully');
      showNotification('Image saved successfully', 'success');

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
    vibrance,
    exposure,
    temperature,
    sharpness,
    vignette,
    highlights,
    allMedia,
    globalIndex,
    isSecureFolder,
    showNotification,
  ]);

  const handleThumbnailClick = (index: number) => {
    setGlobalIndex(index);
    resetZoom();
  };

  const toggleSlideshow = () => {
    setIsSlideshowActive((prev) => !prev);
  };

  const isFavorite = (mediaUrl: string) => favorites.includes(mediaUrl);

  const handleMoveToSecureFolder = async () => {
    const currentMedia = allMedia[globalIndex];
    if (!currentMedia || !currentMedia.path) return;

    const secureFolderCreated = await invoke<boolean>(
      'check_secure_folder_status',
    );
    if (!secureFolderCreated) {
      navigate(`/${ROUTES.LAYOUT.SECURE_FOLDER}`);
      return;
    }

    try {
      const password = prompt('Enter your secure folder password:');
      if (!password) return;

      await invoke('move_to_secure_folder', {
        path: currentMedia.path,
        password,
      });
      showNotification('File moved to secure folder', 'success');
      // Remove the moved item from allMedia
      const newAllMedia = [...allMedia];
      newAllMedia.splice(globalIndex, 1);
      // Update allMedia state (you might need to lift this state up to a parent component)
      // setAllMedia(newAllMedia);
      if (newAllMedia.length === 0) {
        onClose();
      } else {
        setGlobalIndex(Math.min(globalIndex, newAllMedia.length - 1));
      }
    } catch (error) {
      showNotification(`Failed to move file: ${error}`, 'error');
    }
  };

  const handleSetWallpaper = async () => {
    try {
      await invoke('set_wallpaper', { path: allMedia[globalIndex].path });
      showNotification('Wallpaper set successfully', 'success');
    } catch (err: any) {
      showNotification(`Failed to set wallpaper: ${err}`, 'error');
    }
  };

  const handleOpenFolder = async () => {
    try {
      await invoke('open_folder', { path: allMedia[globalIndex].path });
    } catch (err: any) {
      showNotification(`Failed to open folder: ${err}`, 'error');
    }
  };

  const handleOpenWith = async () => {
    try {
      await invoke('open_with', { path: allMedia[globalIndex].path });
    } catch (err: any) {
      showNotification(`Failed to open file: ${err}`, 'error');
    }
  };

  const toggleInfo = () => {
    setShowInfo((prev) => !prev);
  };

  const toggleAdjustMenu = () => {
    setShowAdjustMenu((prev) => !prev);
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-gradient-to-b from-black/95 to-black/98 backdrop-blur-lg">
      <div className="absolute top-4 right-4 z-50 flex items-center gap-3">
        <button
          onClick={toggleInfo}
          className="rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
          aria-label="Show Info"
        >
          <Info className="h-5 w-5" />
        </button>
        <button
          onClick={handleSetWallpaper}
          className="rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
          aria-label="Set as Wallpaper"
        >
          <ImageIcon className="h-5 w-5" />
        </button>
        <button
          onClick={handleOpenFolder}
          className="rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
          aria-label="Open Folder"
        >
          <Folder className="h-5 w-5" />
        </button>
        <button
          onClick={handleOpenWith}
          className="rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
          aria-label="Open With"
        >
          <ExternalLink className="h-5 w-5" />
        </button>
        {!isSecureFolder && (
          <button
            onClick={handleShare}
            className="rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
            aria-label="Share"
          >
            <Share2 className="h-5 w-5" />
          </button>
        )}
        {!isSecureFolder && (
          <button
            onClick={toggleFavorite}
            className={`rounded-full p-2.5 text-white transition-all duration-300 ${
              isFavorite(allMedia[globalIndex].path || '')
                ? 'bg-rose-500/80 hover:bg-rose-600 hover:shadow-lg'
                : 'bg-white/10 hover:bg-white/20 hover:text-white hover:shadow-lg'
            }`}
            aria-label={
              isFavorite(allMedia[globalIndex].path || '')
                ? 'Remove from favorites'
                : 'Add to favorites'
            }
          >
            <Heart
              className={`h-5 w-5 ${isFavorite(allMedia[globalIndex].path || '') ? 'fill-current' : ''}`}
            />
          </button>
        )}
        {type === 'image' && !isSecureFolder && (
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="rounded-full bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
            aria-label="Edit"
          >
            <Edit className="h-5 w-5" />
          </button>
        )}
        {!isSecureFolder && (
          <button
            onClick={handleMoveToSecureFolder}
            className="rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
            aria-label="Move to Secure Folder"
          >
            <Lock className="h-5 w-5" />
          </button>
        )}

        {type === 'image' && (
          <button
            onClick={toggleSlideshow}
            className="flex items-center gap-2 rounded-full bg-indigo-500/70 px-4 py-2 text-white transition-all duration-200 hover:bg-indigo-600/80 hover:shadow-lg"
            aria-label="Toggle Slideshow"
          >
            {isSlideshowActive ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            <span className="text-sm font-medium">
              {isSlideshowActive ? 'Pause' : 'Slideshow'}
            </span>
          </button>
        )}

        <button
          onClick={onClose}
          className="ml-2 rounded-full bg-white/10 p-2.5 text-white/90 transition-all duration-200 hover:bg-white/20 hover:text-white hover:shadow-lg"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
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
            className="relative flex h-full w-full items-center justify-center overflow-hidden"
          >
            {isEditing ? (
              <div className="relative inline-block">
                <ReactCrop
                  crop={crop}
                  onChange={(c) => setCrop(c)}
                  aspect={aspect}
                  onComplete={(c) => setCompletedCrop(c)}
                >
                  <TemperatureFilter temperature={temperature} />
                  <img
                    id="source-image"
                    src={
                      allMedia[globalIndex].url ||
                      allMedia[globalIndex].url ||
                      '/placeholder.svg'
                    }
                    alt={`image-${globalIndex}`}
                    onError={(e) => {
                      const img = e.target as HTMLImageElement;
                      img.onerror = null;
                      img.src =
                        allMedia[globalIndex].thumbnailUrl ||
                        allMedia[globalIndex].url ||
                        '/PictoPy_Logo.png'; // Ensure a valid fallback
                    }}
                    style={{
                      filter: `
                      brightness(${100 + exposure + highlights / 2}%) 
                      contrast(${100 + contrast}%) 
                      saturate(${1 + vibrance / 100}) 
                      hue-rotate(${temperature > 0 ? temperature * 0.25 : temperature * 0.8}deg) 
                      sepia(${Math.abs(temperature) / 200}) 
                      saturate(${temperature > 0 ? 1.2 : 1.0}) 
                      brightness(${temperature > 0 ? 1.05 : 1.0}) 
                      ${sharpness > 0 ? `url(#sharpness)` : ''} 
                      ${filter} 
                      `.trim(),
                      display: 'block',
                      width: '100%',
                    }}
                  />
                  <svg width="0" height="0">
                    <filter id="sharpness">
                      <feConvolveMatrix
                        order="3"
                        kernelMatrix="0 -1 0 -1 5 -1 0 -1 0"
                      />
                    </filter>
                  </svg>
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      background: `radial-gradient(circle, rgba(0,0,0,0) 50%, rgba(0,0,0,${vignette / 100}))`,
                      pointerEvents: 'none',
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      background: `radial-gradient(circle, rgba(255, 255, 255, ${Math.min(highlights / 1000, 0.8)}) 30%, rgba(255, 255, 255, 0) 80%)`,
                      pointerEvents: 'none',
                    }}
                  />
                </ReactCrop>
              </div>
            ) : (
              <img
                src={
                  allMedia[globalIndex].url ||
                  allMedia[globalIndex].thumbnailUrl
                }
                alt={`image-${globalIndex}`}
                draggable={false}
                className="h-full w-full object-contain select-none"
                onError={(e) => {
                  const img = e.target as HTMLImageElement;
                  img.onerror = null;
                  img.src =
                    allMedia[globalIndex].thumbnailUrl ||
                    allMedia[globalIndex].url ||
                    '/PictoPy_Logo.png'; // Ensure a valid fallback
                }}
                style={{
                  transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
                  transition: isDragging
                    ? 'none'
                    : 'transform 0.2s ease-in-out',
                  cursor: isDragging ? 'grabbing' : 'grab',
                }}
              />
            )}
          </div>
        ) : (
          <NetflixStylePlayer
            videoSrc={allMedia[globalIndex].url}
            description=""
            title=""
          />
        )}
        {!isEditing && (
          <>
            <button
              onClick={handlePrevItem}
              className="absolute top-1/2 left-4 z-50 flex items-center rounded-full bg-white/20 p-3 text-white transition-colors duration-200 hover:bg-white/40"
            >
              <ChevronLeft className="h-6 w-6" />
            </button>
            <button
              onClick={handleNextItem}
              className="absolute top-1/2 right-4 z-50 flex items-center rounded-full bg-white/20 p-3 text-white transition-colors duration-200 hover:bg-white/40"
            >
              <ChevronRight className="h-6 w-6" />
            </button>
          </>
        )}
      </div>

      {type === 'image' ? (
        <div className="absolute right-4 bottom-32 flex flex-col gap-4 rounded-xl bg-black/30 p-3 backdrop-blur-md">
          <div className="flex gap-2">
            <button
              onClick={handleZoomOut}
              className="rounded-md bg-white/10 p-2 text-white transition-all duration-200 hover:bg-white/20 hover:shadow-md"
              aria-label="Zoom Out"
            >
              <ZoomOut className="h-5 w-5" />
            </button>
            <button
              onClick={resetZoom}
              className="rounded-md bg-white/10 px-3 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-white/20 hover:shadow-md"
            >
              Reset
            </button>
            <button
              onClick={handleZoomIn}
              className="rounded-md bg-white/10 p-2 text-white transition-all duration-200 hover:bg-white/20 hover:shadow-md"
              aria-label="Zoom In"
            >
              <ZoomIn className="h-5 w-5" />
            </button>
            <button
              onClick={handleRotate}
              className="rounded-md bg-white/10 p-2 text-white transition-all duration-200 hover:bg-white/20 hover:shadow-md"
              aria-label="Rotate"
            >
              <RotateCw className="h-5 w-5" />
            </button>
          </div>
          {isEditing && (
            <>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={handleEditComplete}
                  className="rounded-md bg-emerald-500/70 p-2 text-white transition-all duration-200 hover:bg-emerald-600 hover:shadow-md"
                  aria-label="Confirm Edit"
                >
                  <Check className="h-5 w-5" />
                </button>
                <button
                  onClick={resetEditing}
                  className="rounded-md bg-rose-500/70 p-2 text-white transition-all duration-200 hover:bg-rose-600 hover:shadow-md"
                  aria-label="Cancel Edit"
                >
                  <X className="h-5 w-5" />
                </button>
                <select
                  onChange={(e) => setFilter(e.target.value)}
                  className="rounded-md bg-white/10 px-2 py-2 text-sm text-black transition-all duration-200 hover:bg-white/20"
                >
                  <option value="">No Filter</option>
                  <option value="grayscale(100%)">Grayscale</option>
                  <option value="sepia(100%)">Sepia</option>
                  <option value="invert(100%)">Invert</option>
                  <option value="saturate(200%)">Saturate</option>
                </select>

                <button
                  onClick={toggleAdjustMenu}
                  className="rounded-md bg-white/10 p-2 text-white transition-all duration-200 hover:bg-white/20 hover:shadow-md"
                  aria-label="Adjust"
                >
                  <Sliders className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setonaspect(!onaspect)}
                  className="rounded-md bg-white/20 p-2 text-white transition-colors duration-200 hover:bg-white/40"
                  aria-label="Adjust"
                >
                  <Crops />
                </button>
                {showAdjustMenu && (
                  <div className="absolute bottom-full right-5 mb-2 z-[9999] grid w-64 grid-cols-2 gap-2 rounded-md border bg-gray-500 p-4 hover:border-white lg:grid-cols-1 max-h-60 overflow-y-auto">
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Brightness
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={brightness}
                        onChange={(e) => setBrightness(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Contrast
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={contrast}
                        onChange={(e) => setContrast(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Vibrance
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={vibrance}
                        onChange={(e) => setVibrance(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Exposure
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={exposure}
                        onChange={(e) => setExposure(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Temperature
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={temperature}
                        onChange={(e) => setTemperature(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Sharpness
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={sharpness}
                        onChange={(e) => setSharpness(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Vignette
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={vignette}
                        onChange={(e) => setVignette(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                    <div className="mb-1">
                      <label className="block text-sm font-medium text-white">
                        Highlights
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={highlights}
                        onChange={(e) => setHighlights(Number(e.target.value))}
                        className="h-1 w-full cursor-pointer accent-blue-500"
                      />
                    </div>
                  </div>
                )}
            
                {onaspect && (
                  <div className="absolute bottom-full mb-2 w-32 rounded-md bg-white/20 backdrop-blur-md sm:right-1">
                    <div className="mt-1 mb-1 flex flex-col justify-center gap-1">
                      <div
                        className="w-full p-2 text-center hover:bg-slate-400"
                        onClick={() => setaspect(16 / 9)}
                      >
                        16/9
                      </div>
                      <div
                        className="w-full p-2 text-center hover:bg-slate-400"
                        onClick={() => setaspect(3 / 4)}
                      >
                        3/4
                      </div>
                      <div
                        className="w-full p-2 text-center hover:bg-slate-400"
                        onClick={() => setaspect(1 / 1)}
                      >
                        1:1
                      </div>
                      <div
                        className="flex w-full justify-center p-2 text-center hover:bg-slate-400"
                        onClick={() => setaspect(9 / 16)}
                      >
                        <Instagram></Instagram>
                      </div>
                      <div
                        className="flex w-full justify-center p-2 text-center hover:bg-slate-400"
                        onClick={() => setaspect(undefined)}
                      >
                        <X></X>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      ) : null}

      {/* Adjust menu popup with improved styling */}
      {showAdjustMenu && (
        <button
          onClick={toggleAdjustMenu}
          className="mt-2 w-full rounded-md bg-white/20 py-1.5 text-xs font-medium text-white transition-all hover:bg-white/30"
        >
          Close
        </button>
      )}

      {/* Thumbnails with improved styling */}
      {type === 'image' && (
        <div className="absolute bottom-0 w-full">
          <div className="flex w-full items-center justify-center gap-2 overflow-x-auto bg-black/50 px-4 py-3 opacity-0 transition-all duration-300 hover:opacity-100">
            {allMedia.map((media, index) => (
              <div
                key={index}
                onClick={() => handleThumbnailClick(index)}
                className={`relative h-16 w-24 flex-shrink-0 overflow-hidden rounded-lg ${
                  index === globalIndex
                    ? 'ring-2 ring-blue-500 ring-offset-1 ring-offset-black'
                    : 'opacity-70 hover:opacity-100'
                } cursor-pointer transition-all duration-200 hover:scale-105`}
              >
                {isFavorite(media.path || '') && (
                  <div className="absolute top-1 right-1 z-10 rounded-full bg-black/30 p-0.5">
                    <Heart className="h-3 w-3 fill-current text-rose-500" />
                  </div>
                )}
                {type === 'image' ? (
                  <img
                    src={media.thumbnailUrl || '/placeholder.svg'}
                    alt={`thumbnail-${index}`}
                    className="h-full w-full object-cover"
                  />
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Improved notification */}
      {notification && (
        <div
          className={`fixed top-4 left-1/2 -translate-x-1/2 transform rounded-full ${
            notification.type === 'success' ? 'bg-emerald-500' : 'bg-rose-500'
          } animate-in fade-in px-6 py-2 text-sm font-medium text-white shadow-lg transition-all duration-300`}
        >
          {notification.message}
        </div>
      )}
      {/* Improved info panel */}
      {showInfo && (
        <div className="animate-in slide-in-from-left absolute top-4 left-4 z-50 max-w-md rounded-xl bg-black/50 p-4 backdrop-blur-lg transition-all duration-300">
          <h3 className="mb-3 text-lg font-medium text-white">
            File Information
          </h3>
          <div className="space-y-1.5 text-sm text-white/80">
            <p className="truncate">
              <span className="text-white/60">Path:</span>{' '}
              {allMedia[globalIndex].path}
            </p>
            <p>
              <span className="text-white/60">Type:</span> {type}
            </p>
            <p>
              <span className="text-white/60">Secure:</span>{' '}
              {isSecureFolder ? 'Yes' : 'No'}
            </p>
            <p>
              <span className="text-white/60">Index:</span> {globalIndex + 1} of{' '}
              {allMedia.length}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaView;

const TemperatureFilter = ({
  temperature,
  intensity = 1.5,
}: {
  temperature: number;
  intensity?: number;
}) => {
  // Amplify the temperature value
  const factor = (temperature * intensity) / 100;
  // Calculate red and blue multipliers.
  // For positive temperature, red increases and blue decreases.
  // For negative temperature, red decreases and blue increases.
  const rMult = (1 + factor).toFixed(2);
  const bMult = (1 - factor).toFixed(2);

  return (
    <svg width="0" height="0" style={{ position: 'absolute' }}>
      <filter id="temp">
        <feColorMatrix
          type="matrix"
          values={`${rMult} 0 0 0 0  0 1 0 0 0  0 0 ${bMult} 0 0  0 0 0 1 0`}
        />
      </filter>
    </svg>
  );
};
