import { useEffect, useState } from 'react';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchMemories } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { ClockFading, MapPin, Calendar } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Image } from '@/types/Media';
import { MediaView } from '@/components/Media/MediaView';

interface MemoryImage {
  id: string;
  path: string;
  thumbnailPath: string;
  metadata: any;
}

interface Memory {
  id: string;
  title: string;
  date: string;
  type: 'on_this_day' | 'location';
  image_count: number;
  images: MemoryImage[];
  latitude?: number;
  longitude?: number;
}

const Memories = () => {
  const [selectedMemoryImages, setSelectedMemoryImages] = useState<Image[]>([]);
  const [isImageViewOpen, setIsImageViewOpen] = useState(false);

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['memories'],
    queryFn: () => fetchMemories(),
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading memories',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load memories. Please try again later.',
    },
  );

  const memories: Memory[] = (data?.data as Memory[]) || [];

  const handleMemoryClick = (memory: Memory) => {
    // Convert memory images to Image format for MediaView
    const images: Image[] = memory.images.map((img) => ({
      id: img.id,
      path: img.path,
      thumbnailPath: img.thumbnailPath,
      folder_id: '',
      isTagged: false,
      metadata: img.metadata,
    }));

    setSelectedMemoryImages(images);
    setIsImageViewOpen(true);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (memories.length === 0 && !isLoading) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="text-center">
          <div className="bg-muted/50 mb-6 flex h-32 w-32 items-center justify-center rounded-full mx-auto">
            <ClockFading className="h-12 w-12 text-muted-foreground" />
          </div>
          <h2 className="text-foreground mb-3 text-xl font-semibold">
            No Memories Yet
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Memories will appear here as you add more photos to your gallery.
            They are automatically grouped by date and location.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Memories</h1>
        <p className="text-muted-foreground mt-2">
          Relive your favorite moments, automatically organized by time and place
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {memories.map((memory) => (
          <Card
            key={memory.id}
            className="group cursor-pointer transition-all hover:shadow-lg"
            onClick={() => handleMemoryClick(memory)}
          >
            <CardHeader className="p-0">
              <div className="relative aspect-video w-full overflow-hidden rounded-t-xl">
                {/* Main image */}
                {memory.images[0] && (
                  <img
                    src={convertFileSrc(
                      memory.images[0].thumbnailPath ||
                        memory.images[0].path ||
                        '/placeholder.svg',
                    )}
                    alt={memory.title}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                  />
                )}

                {/* Overlay with gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />

                {/* Additional images indicator */}
                {memory.images.length > 1 && (
                  <div className="absolute top-2 right-2 flex gap-1">
                    {memory.images.slice(1, 4).map((img, idx) => (
                      <div
                        key={img.id}
                        className="h-12 w-12 overflow-hidden rounded border-2 border-white/50"
                      >
                        <img
                          src={convertFileSrc(
                            img.thumbnailPath || img.path || '/placeholder.svg',
                          )}
                          alt=""
                          className="h-full w-full object-cover"
                        />
                      </div>
                    ))}
                    {memory.image_count > 4 && (
                      <div className="bg-black/70 flex h-12 w-12 items-center justify-center rounded border-2 border-white/50 text-xs font-semibold text-white">
                        +{memory.image_count - 4}
                      </div>
                    )}
                  </div>
                )}

                {/* Memory type icon */}
                <div className="absolute bottom-2 left-2">
                  {memory.type === 'on_this_day' ? (
                    <Calendar className="h-5 w-5 text-white" />
                  ) : (
                    <MapPin className="h-5 w-5 text-white" />
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-4">
              <h3 className="mb-2 text-lg font-semibold line-clamp-2">
                {memory.title}
              </h3>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <ClockFading className="h-4 w-4" />
                <span>{formatDate(memory.date)}</span>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {memory.image_count} photo{memory.image_count !== 1 ? 's' : ''}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {isImageViewOpen && (
        <MediaView
          images={selectedMemoryImages}
          onClose={() => {
            setIsImageViewOpen(false);
            setSelectedMemoryImages([]);
          }}
        />
      )}
    </div>
  );
};

export default Memories;
