import { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { Calendar, MapPin, Image as ImageIcon, Sparkles } from 'lucide-react';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllMemories } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { convertFileSrc } from '@tauri-apps/api/core';
import { cn } from '@/lib/utils';

interface MemoryImage {
  id: string;
  path: string;
  thumbnail: string;
  date: string;
  location?: string;
}

interface Memory {
  id: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  image_count: number;
  images: MemoryImage[];
}

const MemoryCard = ({ memory }: { memory: Memory }) => {
  const [imageLoadError, setImageLoadError] = useState<Set<number>>(new Set());

  const handleImageError = (index: number) => {
    setImageLoadError((prev) => new Set(prev).add(index));
  };

  // Display up to 5 images in a grid layout
  const displayImages = memory.images.slice(0, 5);

  return (
    <Card className="group overflow-hidden transition-all hover:shadow-lg cursor-pointer">
      <CardContent className="p-0">
        {/* Image Grid */}
        <div className="relative">
          {displayImages.length === 1 && (
            <div className="aspect-[16/9] w-full overflow-hidden">
              <img
                src={
                  imageLoadError.has(0)
                    ? '/placeholder.svg'
                    : convertFileSrc(displayImages[0].thumbnail || displayImages[0].path)
                }
                alt={memory.title}
                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                onError={() => handleImageError(0)}
              />
            </div>
          )}

          {displayImages.length === 2 && (
            <div className="grid grid-cols-2 gap-1">
              {displayImages.map((img, idx) => (
                <div key={img.id} className="aspect-square overflow-hidden">
                  <img
                    src={
                      imageLoadError.has(idx)
                        ? '/placeholder.svg'
                        : convertFileSrc(img.thumbnail || img.path)
                    }
                    alt={`Memory ${idx + 1}`}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={() => handleImageError(idx)}
                  />
                </div>
              ))}
            </div>
          )}

          {displayImages.length === 3 && (
            <div className="grid grid-cols-2 gap-1">
              <div className="row-span-2 overflow-hidden">
                <img
                  src={
                    imageLoadError.has(0)
                      ? '/placeholder.svg'
                      : convertFileSrc(displayImages[0].thumbnail || displayImages[0].path)
                  }
                  alt="Memory 1"
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  onError={() => handleImageError(0)}
                />
              </div>
              {displayImages.slice(1).map((img, idx) => (
                <div key={img.id} className="aspect-square overflow-hidden">
                  <img
                    src={
                      imageLoadError.has(idx + 1)
                        ? '/placeholder.svg'
                        : convertFileSrc(img.thumbnail || img.path)
                    }
                    alt={`Memory ${idx + 2}`}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={() => handleImageError(idx + 1)}
                  />
                </div>
              ))}
            </div>
          )}

          {displayImages.length >= 4 && (
            <div className="grid grid-cols-3 gap-1">
              <div className="col-span-2 row-span-2 overflow-hidden">
                <img
                  src={
                    imageLoadError.has(0)
                      ? '/placeholder.svg'
                      : convertFileSrc(displayImages[0].thumbnail || displayImages[0].path)
                  }
                  alt="Memory 1"
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  onError={() => handleImageError(0)}
                />
              </div>
              {displayImages.slice(1, 5).map((img, idx) => (
                <div key={img.id} className="aspect-square overflow-hidden">
                  <img
                    src={
                      imageLoadError.has(idx + 1)
                        ? '/placeholder.svg'
                        : convertFileSrc(img.thumbnail || img.path)
                    }
                    alt={`Memory ${idx + 2}`}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={() => handleImageError(idx + 1)}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

          {/* Image count badge */}
          <div className="absolute top-3 right-3">
            <Badge variant="secondary" className="bg-black/50 text-white backdrop-blur-sm">
              <ImageIcon className="mr-1 h-3 w-3" />
              {memory.image_count}
            </Badge>
          </div>
        </div>

        {/* Memory Info */}
        <div className="p-4">
          <h3 className="mb-2 text-lg font-semibold line-clamp-2">{memory.title}</h3>
          <p className="mb-3 text-sm text-muted-foreground line-clamp-1">
            {memory.description}
          </p>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>
                {new Date(memory.start_date).toLocaleDateString('en-US', {
                  month: 'short',
                  year: 'numeric',
                })}
              </span>
            </div>
            {memory.location && memory.location !== 'Unknown Location' && (
              <div className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                <span className="line-clamp-1">{memory.location}</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const MemoryCardSkeleton = () => (
  <Card className="overflow-hidden">
    <CardContent className="p-0">
      <Skeleton className="aspect-[16/9] w-full" />
      <div className="p-4 space-y-2">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <div className="flex gap-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
    </CardContent>
  </Card>
);

const EmptyMemoriesState = () => (
  <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4">
    <div className="rounded-full bg-primary/10 p-6 mb-4">
      <Sparkles className="h-12 w-12 text-primary" />
    </div>
    <h2 className="text-2xl font-semibold mb-2">No Memories Yet</h2>
    <p className="text-muted-foreground max-w-md">
      Your memories will appear here automatically as you add more photos with dates and locations.
      Keep capturing moments!
    </p>
  </div>
);

const Memories = () => {
  const dispatch = useDispatch();
  const [memories, setMemories] = useState<Memory[]>([]);

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['memories'],
    queryFn: () => fetchAllMemories(),
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

  useEffect(() => {
    if (isSuccess && data?.data) {
      // Validate data structure before setting state
      const memoriesData = data.data;
      
      if (Array.isArray(memoriesData)) {
        // Filter and validate each memory object
        const validMemories = memoriesData.filter((item: any) => {
          return (
            item &&
            typeof item === 'object' &&
            typeof item.id === 'string' &&
            typeof item.title === 'string' &&
            Array.isArray(item.images)
          );
        }) as Memory[];
        
        setMemories(validMemories);
      }
    }
  }, [data, isSuccess]);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="mb-6 pr-6">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <h1 className="text-3xl font-bold">Memories</h1>
        </div>
        <p className="text-muted-foreground">
          Relive your favorite moments, automatically organized by time and location
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto hide-scrollbar pr-6">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <MemoryCardSkeleton key={i} />
            ))}
          </div>
        ) : memories.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-6">
            {memories.map((memory) => (
              <MemoryCard key={memory.id} memory={memory} />
            ))}
          </div>
        ) : (
          <EmptyMemoriesState />
        )}
      </div>
    </div>
  );
};

export default Memories;
