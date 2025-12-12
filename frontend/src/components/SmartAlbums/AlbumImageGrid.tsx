import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Heart,
  ZoomIn,
  X,
  ChevronLeft,
  ChevronRight,
  Loader2,
  ImageOff,
} from 'lucide-react';
import { getSmartAlbumImages } from '@/api/api-functions/smart_albums';
import type { AlbumImage } from '@/api/api-functions/smart_albums';
import { BatchOperationsToolbar } from './BatchOperationsToolbar';
import { BACKEND_URL } from '@/config/Backend';

interface AlbumImageGridProps {
  albumId: string;
  pageSize?: number;
  onToggleFavorite?: (imageId: string, isFavorite: boolean) => void;
}



const getThumbnailUrl = (imageId: string): string => {
  return `${BACKEND_URL}/images/${imageId}/thumbnail`;
};


const getFullImageUrl = (imageId: string): string => {
  return `${BACKEND_URL}/images/${imageId}`;
};

export const AlbumImageGrid: React.FC<AlbumImageGridProps> = ({
  albumId,
  pageSize = 20,
  onToggleFavorite,
}) => {
  const [images, setImages] = useState<AlbumImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);
  const isLoadingRef = useRef(false);


  const fetchImages = useCallback(
    async (currentOffset: number, append: boolean = false) => {
      if (isLoadingRef.current) return;

      isLoadingRef.current = true;
      setLoading(true);

      try {
        const data = await getSmartAlbumImages(albumId, pageSize, currentOffset);

        if (append) {
          setImages((prev) => [...prev, ...data]);
        } else {
          setImages(data);
        }

        setHasMore(data.length === pageSize);
        setOffset(currentOffset + data.length);
      } catch (error) {
        console.error('Failed to fetch images:', error);
      } finally {
        setLoading(false);
        isLoadingRef.current = false;
      }
    },
    [albumId, pageSize]
  );


  useEffect(() => {
    setImages([]);
    setOffset(0);
    setHasMore(true);
    setSelectedImages(new Set());
    setImageErrors(new Set());
    fetchImages(0, false);
  }, [albumId, fetchImages]);


  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoadingRef.current) {
          fetchImages(offset, true);
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [offset, hasMore, fetchImages]);


  useEffect(() => {
    if (!lightboxOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
          goToNext();
          break;
        case 'ArrowLeft':
          goToPrevious();
          break;
        case 'Escape':
          closeLightbox();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lightboxOpen, images.length]);

 
  const handleImageError = useCallback((imageId: string) => {
    console.error(`Failed to load image: ${imageId}`);
    setImageErrors((prev) => new Set(prev).add(imageId));
  }, []);

 
  const handleToggleSelect = useCallback((imageId: string) => {
    setSelectedImages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(imageId)) {
        newSet.delete(imageId);
      } else {
        newSet.add(imageId);
      }
      return newSet;
    });
  }, []);


  const handleSelectAll = useCallback(() => {
    setSelectedImages(new Set(images.map((img) => img.id)));
  }, [images]);


  const handleDeselectAll = useCallback(() => {
    setSelectedImages(new Set());
  }, []);


  const handleBatchMarkFavorite = useCallback(async () => {
    if (!onToggleFavorite) return;

    const promises = Array.from(selectedImages).map((imageId) => {
      const image = images.find((img) => img.id === imageId);
      if (image && !image.isFavourite) {
        return onToggleFavorite(imageId, false);
      }
      return Promise.resolve();
    });

    await Promise.allSettled(promises);
    setSelectedImages(new Set());
  }, [selectedImages, images, onToggleFavorite]);


  const handleBatchUnmarkFavorite = useCallback(async () => {
    if (!onToggleFavorite) return;

    const promises = Array.from(selectedImages).map((imageId) => {
      const image = images.find((img) => img.id === imageId);
      if (image && image.isFavourite) {
        return onToggleFavorite(imageId, true);
      }
      return Promise.resolve();
    });

    await Promise.allSettled(promises);
    setSelectedImages(new Set());
  }, [selectedImages, images, onToggleFavorite]);


  const handleBatchDelete = useCallback(async () => {
    if (!window.confirm(`Delete ${selectedImages.size} selected images from album?`)) {
      return;
    }
    
    console.log('Batch delete:', Array.from(selectedImages));
    setSelectedImages(new Set());
  }, [selectedImages]);

  
  const handleToggleFavorite = useCallback(
    (imageId: string, isFavorite: boolean) => {
      if (onToggleFavorite) {
        onToggleFavorite(imageId, isFavorite);
      }
      setImages((prev) =>
        prev.map((img) =>
          img.id === imageId ? { ...img, isFavourite: !isFavorite } : img
        )
      );
    },
    [onToggleFavorite]
  );

  const openLightbox = useCallback((index: number) => {
    setCurrentImageIndex(index);
    setLightboxOpen(true);
  }, []);

 
  const closeLightbox = useCallback(() => {
    setLightboxOpen(false);
  }, []);


  const goToNext = useCallback(() => {
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  }, [images.length]);

 
  const goToPrevious = useCallback(() => {
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  }, [images.length]);

 
  if (images.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-500">
        <ImageOff className="w-20 h-20 mb-4 text-gray-300" />
        <h3 className="text-xl font-semibold mb-2">No images in this album</h3>
        <p className="text-sm">
          Images will appear here automatically when they match the album criteria
        </p>
      </div>
    );
  }

  return (
    <>
      <BatchOperationsToolbar
        selectedCount={selectedImages.size}
        totalCount={images.length}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
        onMarkFavorite={handleBatchMarkFavorite}
        onUnmarkFavorite={handleBatchUnmarkFavorite}
        onDelete={handleBatchDelete}
      />

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {images.map((image, index) => {
          const hasError = imageErrors.has(image.id);
          const isSelected = selectedImages.has(image.id);

          return (
            <div key={image.id} className="relative group">
              <Card className="overflow-hidden cursor-pointer transition-transform hover:scale-105">
                {hasError ? (
                  <div className="w-full aspect-square bg-gray-200 flex items-center justify-center">
                    <ImageOff className="w-12 h-12 text-gray-400" />
                  </div>
                ) : (
                  <img
                    src={getThumbnailUrl(image.id)}
                    alt={`Image ${index + 1}`}
                    className="w-full aspect-square object-cover"
                    onClick={() => openLightbox(index)}
                    onError={() => handleImageError(image.id)}
                    loading="lazy"
                  />
                )}

                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-2">
                  <div className="flex justify-between">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleSelect(image.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="h-5 w-5 rounded border-2 border-white bg-white cursor-pointer accent-blue-600"
                      aria-label={`Select image ${index + 1}`}
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-white hover:bg-white/20"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleFavorite(image.id, image.isFavourite);
                      }}
                      aria-label={image.isFavourite ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      <Heart
                        className={`h-5 w-5 ${
                          image.isFavourite ? 'fill-red-500 text-red-500' : ''
                        }`}
                      />
                    </Button>
                  </div>

                  <div className="flex justify-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-white hover:bg-white/20"
                      onClick={() => openLightbox(index)}
                      title="View full size"
                      aria-label="View full size"
                    >
                      <ZoomIn className="h-5 w-5" />
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          );
        })}
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      )}

      {hasMore && <div ref={loadMoreRef} className="h-5" aria-hidden="true" />}

    
      {lightboxOpen && images[currentImageIndex] && (
        <div
          className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center"
          onClick={closeLightbox}
          role="dialog"
          aria-modal="true"
          aria-label="Image viewer"
        >
          <Button
            variant="ghost"
            size="sm"
            className="absolute top-4 right-4 h-10 w-10 p-0 text-white hover:bg-white/10"
            onClick={closeLightbox}
            aria-label="Close viewer"
          >
            <X className="h-6 w-6" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="absolute top-4 left-4 h-10 w-10 p-0 text-white hover:bg-white/10"
            onClick={(e) => {
              e.stopPropagation();
              handleToggleFavorite(
                images[currentImageIndex].id,
                images[currentImageIndex].isFavourite
              );
            }}
            aria-label={
              images[currentImageIndex].isFavourite
                ? 'Remove from favorites'
                : 'Add to favorites'
            }
          >
            <Heart
              className={`h-6 w-6 ${
                images[currentImageIndex].isFavourite ? 'fill-red-500 text-red-500' : ''
              }`}
            />
          </Button>

          {images.length > 1 && (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="absolute left-4 h-12 w-12 p-0 text-white hover:bg-white/10"
                onClick={(e) => {
                  e.stopPropagation();
                  goToPrevious();
                }}
                aria-label="Previous image"
              >
                <ChevronLeft className="h-8 w-8" />
              </Button>

              <Button
                variant="ghost"
                size="sm"
                className="absolute right-4 h-12 w-12 p-0 text-white hover:bg-white/10"
                onClick={(e) => {
                  e.stopPropagation();
                  goToNext();
                }}
                aria-label="Next image"
              >
                <ChevronRight className="h-8 w-8" />
              </Button>
            </>
          )}

          <img
            src={getFullImageUrl(images[currentImageIndex].id)}
            alt={`Image ${currentImageIndex + 1}`}
            className="max-w-[90%] max-h-[90%] object-contain"
            onClick={(e) => e.stopPropagation()}
            onError={() => handleImageError(images[currentImageIndex].id)}
          />

          <Badge className="absolute bottom-4 bg-black/60 text-white px-4 py-2">
            {currentImageIndex + 1} / {images.length}
          </Badge>
        </div>
      )}
    </>
  );
};