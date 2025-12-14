// src/pages/Memories/MemoryDetail.tsx

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { ArrowLeft, Calendar, MapPin, Images as ImagesIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { getMemoryDetail } from '@/api/api-functions/memories';
import { Image } from '@/types/Media';
import { ImageInMemory } from '@/types/Memory';
import { MediaView } from '@/components/Media/MediaView';
import { convertFileSrc } from '@tauri-apps/api/core';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export const MemoryDetail = () => {
  const { memoryId } = useParams<{ memoryId: string }>();
  const navigate = useNavigate();
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(
    null,
  );

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['memory', memoryId],
    queryFn: () => getMemoryDetail(memoryId!),
    enabled: !!memoryId,
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading memory',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load memory. Please try again.',
    },
  );

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">Loading memory...</div>
      </div>
    );
  }

  if (!data?.data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-muted-foreground">Memory not found</p>
          <Button onClick={() => navigate('/memories')} className="mt-4">
            Back to Memories
          </Button>
        </div>
      </div>
    );
  }

  const memory = data.data;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatDateRange = () => {
    const start = formatDate(memory.start_date);
    const end = formatDate(memory.end_date);
    return start === end ? start : `${start} - ${end}`;
  };

  // Convert ImageInMemory to Image type for MediaView
  const convertToImages = (memoryImages: ImageInMemory[]): Image[] => {
    return memoryImages.map((img) => ({
      id: img.id,
      path: img.path,
      thumbnailPath: img.thumbnailPath,
      folder_id: '',
      isTagged: false,
      metadata: img.metadata,
    }));
  };

  const images = convertToImages(memory.images);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b p-6">
        <Button
          variant="ghost"
          onClick={() => navigate('/memories')}
          className="mb-4 gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Memories
        </Button>

        <h1 className="mb-4 text-3xl font-bold">{memory.title}</h1>

        <div className="flex flex-wrap gap-4 text-muted-foreground">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            <span>{formatDateRange()}</span>
          </div>

          {memory.location && (
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              <span>{memory.location}</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <ImagesIcon className="h-5 w-5" />
            <span>{memory.total_photos} photos</span>
          </div>
        </div>
      </div>

      {/* Photo Grid */}
      <div className="hide-scrollbar flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {memory.images.map((image, index) => (
            <div
              key={image.id}
              onClick={() => setSelectedImageIndex(index)}
              className="group relative aspect-square cursor-pointer overflow-hidden rounded-lg bg-muted transition-all hover:scale-105 hover:shadow-lg"
            >
              <img
                src={convertFileSrc(image.thumbnailPath)}
                alt={image.metadata.name}
                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
              />

              {/* Representative badge */}
              {image.is_representative && (
                <div className="absolute left-2 top-2 rounded-full bg-primary/90 px-2 py-1 text-xs font-medium text-primary-foreground">
                  Featured
                </div>
              )}

              {/* Hover overlay */}
              <div className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/10" />
            </div>
          ))}
        </div>
      </div>

      {/* Media Viewer */}
      {selectedImageIndex !== null && (
        <MediaView
          images={images}
          onClose={() => setSelectedImageIndex(null)}
          type="image"
        />
      )}
    </div>
  );
};