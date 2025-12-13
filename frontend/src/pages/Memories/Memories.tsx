import { useEffect, useState } from 'react';
import { Calendar, MapPin, Image as ImageIcon, Sparkles, ArrowLeft, X } from 'lucide-react';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllMemories, fetchMemoryImages } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { convertFileSrc } from '@tauri-apps/api/core';

interface MemoryImage {
  id: string;
  path: string;
  thumbnail?: string;
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

const MemoryCard = ({ memory, onClick }: { memory: Memory; onClick: () => void }) => {
  const [imageLoadError, setImageLoadError] = useState<Set<number>>(new Set());

  const handleImageError = (index: number) => {
    setImageLoadError((prev) => new Set(prev).add(index));
  };

  // Display up to 5 images in a grid layout
  const displayImages = memory.images.slice(0, 5);

  return (
    <Card 
      className="group overflow-hidden transition-all hover:shadow-lg cursor-pointer"
      onClick={onClick}
    >
      <CardContent className="p-0">
        {/* Image Grid - Fixed aspect ratio container for consistency */}
        <div className="relative aspect-[4/3] overflow-hidden">
          {displayImages.length === 1 && (
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
          )}

          {displayImages.length === 2 && (
            <div className="grid grid-cols-2 gap-1 h-full">
              {displayImages.map((img, idx) => (
                <div key={img.id} className="overflow-hidden">
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
            <div className="grid grid-cols-2 gap-1 h-full">
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
                <div key={img.id} className="overflow-hidden">
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
            <div className="grid grid-cols-3 grid-rows-2 gap-1 h-full">
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
              {displayImages.slice(1, 3).map((img, idx) => (
                <div key={img.id} className="overflow-hidden">
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

const MemoryDetailView = ({ 
  memory, 
  onBack 
}: { 
  memory: Memory; 
  onBack: () => void;
}) => {
  const [imageLoadError, setImageLoadError] = useState<Set<number>>(new Set());
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(null);
  const [allImages, setAllImages] = useState<MemoryImage[]>(memory.images);
  const [isLoadingImages, setIsLoadingImages] = useState(true);

  // Fetch all images for this memory
  useEffect(() => {
    const loadAllImages = async () => {
      setIsLoadingImages(true);
      try {
        const response = await fetchMemoryImages(memory.id);
        if (response.success && response.data && Array.isArray(response.data)) {
          // Map the response to MemoryImage format
          const images: MemoryImage[] = response.data.map((img: any) => ({
            id: img.id,
            path: img.path,
            thumbnail: img.thumbnail,
            date: img.metadata?.date_created || '',
            location: img.metadata?.location,
          }));
          setAllImages(images);
        }
      } catch (error) {
        console.error('Failed to load memory images:', error);
        // Fall back to the preview images
        setAllImages(memory.images);
      } finally {
        setIsLoadingImages(false);
      }
    };

    loadAllImages();
  }, [memory.id, memory.images]);

  const handleImageError = (index: number) => {
    setImageLoadError((prev) => new Set(prev).add(index));
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="mb-6 pr-6">
        <Button 
          variant="ghost" 
          onClick={onBack}
          className="mb-4 -ml-2"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Memories
        </Button>
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <h1 className="text-3xl font-bold">{memory.title}</h1>
        </div>
        <p className="text-muted-foreground">{memory.description}</p>
        <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            <span>
              {new Date(memory.start_date).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric',
              })}
              {memory.start_date !== memory.end_date && (
                <> - {new Date(memory.end_date).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}</>
              )}
            </span>
          </div>
          {memory.location && memory.location !== 'Unknown Location' && (
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              <span>{memory.location}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <ImageIcon className="h-4 w-4" />
            <span>{memory.image_count} photos</span>
          </div>
        </div>
      </div>

      {/* Image Grid */}
      <div className="flex-1 overflow-y-auto hide-scrollbar pr-6">
        {isLoadingImages ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-6">
            {[...Array(Math.min(memory.image_count, 12))].map((_, i) => (
              <Skeleton key={i} className="aspect-square rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-6">
            {allImages.map((img, idx) => (
              <div 
                key={img.id} 
                className="aspect-square overflow-hidden rounded-lg cursor-pointer group"
                onClick={() => setSelectedImageIndex(idx)}
              >
                <img
                  src={
                    imageLoadError.has(idx)
                      ? '/placeholder.svg'
                      : convertFileSrc(img.thumbnail || img.path)
                  }
                  alt={`Photo ${idx + 1}`}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  onError={() => handleImageError(idx)}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Full Image Modal */}
      {selectedImageIndex !== null && allImages[selectedImageIndex] && (
        <div 
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={() => setSelectedImageIndex(null)}
        >
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4 text-white hover:bg-white/20"
            onClick={() => setSelectedImageIndex(null)}
          >
            <X className="h-6 w-6" />
          </Button>
          <img
            src={convertFileSrc(allImages[selectedImageIndex].path)}
            alt={`Photo ${selectedImageIndex + 1}`}
            className="max-h-[90vh] max-w-[90vw] object-contain"
            onClick={(e) => e.stopPropagation()}
          />
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white text-sm">
            {selectedImageIndex + 1} / {allImages.length}
          </div>
        </div>
      )}
    </div>
  );
};

const Memories = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

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

  // If a memory is selected, show the detail view
  if (selectedMemory) {
    return (
      <MemoryDetailView 
        memory={selectedMemory} 
        onBack={() => setSelectedMemory(null)} 
      />
    );
  }

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
              <MemoryCard 
                key={memory.id} 
                memory={memory} 
                onClick={() => setSelectedMemory(memory)}
              />
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
