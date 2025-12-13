import { useState, useEffect } from 'react';
import { Memory } from '@/types/Memory';
import { Button } from '@/components/ui/button';
import { X, Calendar, MapPin, Images } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/core';
import { fetchAllImages } from '@/api/api-functions';
import { Image } from '@/types/Media';
import { MediaView } from '@/components/Media/MediaView';
import { useDispatch, useSelector } from 'react-redux';
import { setImages, setCurrentViewIndex } from '@/features/imageSlice';
import {
  selectCurrentViewIndex,
  selectImages,
} from '@/features/imageSelectors';

interface MemoryDetailViewProps {
  memory: Memory;
  onClose: () => void;
}

export function MemoryDetailView({ memory, onClose }: MemoryDetailViewProps) {
  const [images, setLocalImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const dispatch = useDispatch();
  const currentViewIndex = useSelector(selectCurrentViewIndex);
  const reduxImages = useSelector(selectImages);
  const showImageViewer = currentViewIndex >= 0;

  // Fetch all images and filter to memory's media IDs
  useEffect(() => {
    const loadImages = async () => {
      try {
        setLoading(true);
        const response = await fetchAllImages();
        const allImages = (response.data as Image[]) || [];

        // Filter to only images in this memory
        const memoryImages = allImages.filter((img) =>
          memory.media_ids.includes(img.id),
        );

        // Sort by date to maintain chronological order
        memoryImages.sort((a, b) => {
          const dateA = a.metadata?.date_created || '';
          const dateB = b.metadata?.date_created || '';
          return dateA.localeCompare(dateB);
        });

        setLocalImages(memoryImages);
        // Set images in Redux for MediaView
        dispatch(setImages(memoryImages));
      } catch (error) {
        console.error('Error loading memory images:', error);
      } finally {
        setLoading(false);
      }
    };

    loadImages();
  }, [memory.media_ids]);

  const handleImageClick = (index: number) => {
    dispatch(setCurrentViewIndex(index));
  };

  const formatDateRange = () => {
    const startDate = new Date(memory.date_range.start);
    const endDate = new Date(memory.date_range.end);
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };

    if (startDate.toDateString() === endDate.toDateString()) {
      return startDate.toLocaleDateString('en-US', options);
    }
    return `${startDate.toLocaleDateString('en-US', options)} - ${endDate.toLocaleDateString('en-US', options)}`;
  };

  if (showImageViewer && reduxImages.length > 0) {
    return (
      <MediaView
        onClose={() => {
          dispatch(setCurrentViewIndex(-1));
        }}
        images={reduxImages}
        type="image"
      />
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-card border-b p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-2xl font-bold">{memory.title}</h1>
            <div className="text-muted-foreground mt-2 flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center gap-1.5">
                <Calendar className="h-4 w-4" />
                <span>{formatDateRange()}</span>
              </div>
              {memory.location && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4" />
                  <span>{memory.location}</span>
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <Images className="h-4 w-4" />
                <span>
                  {memory.media_count}{' '}
                  {memory.media_count === 1 ? 'photo' : 'photos'}
                </span>
              </div>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Image Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-muted-foreground">Loading photos...</p>
          </div>
        ) : images.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-muted-foreground">
              No photos found in this memory.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {images.map((image, index) => (
              <div
                key={image.id}
                className="group bg-card relative cursor-pointer overflow-hidden rounded-lg border transition-all hover:shadow-lg"
                onClick={() => handleImageClick(index)}
              >
                <div className="aspect-square w-full">
                  <img
                    src={convertFileSrc(image.thumbnailPath || image.path)}
                    alt={`Memory photo ${index + 1}`}
                    className="h-full w-full object-cover transition-transform group-hover:scale-105"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
