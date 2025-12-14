import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Memory, Image } from '@/types/Media';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllMemories } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import { MediaView } from '@/components/Media/MediaView';
import { selectIsImageViewOpen } from '@/features/imageSelectors';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Calendar, MapPin, ImageIcon, Sparkles } from 'lucide-react';
import { formatDateRange } from '@/utils/memoryUtils';

const Memories = () => {
  const dispatch = useDispatch();
  const [selectedMemoryImages, setSelectedMemoryImages] = useState<Image[]>([]);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);

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

  const memories: Memory[] = data?.data || [];

  const handleMemoryClick = (memory: Memory) => {
    setSelectedMemoryImages(memory.images);
    dispatch(setImages(memory.images));
    dispatch(setCurrentViewIndex(0));
  };

  const getMemoryIcon = (type: Memory['memory_type']) => {
    if (type === 'on_this_day') return <Calendar className="h-5 w-5" />;
    if (type === 'trip') return <MapPin className="h-5 w-5" />;
    return <ImageIcon className="h-5 w-5" />;
  };

  const getMemoryBadge = (type: Memory['memory_type']) => {
    if (type === 'on_this_day') {
      return (
        <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
          On This Day
        </Badge>
      );
    }
    if (type === 'trip') {
      return (
        <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
          Trip
        </Badge>
      );
    }
    return <Badge>Memory</Badge>;
  };

  if (!isLoading && memories.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8">
        <div className="mb-6 rounded-full bg-gray-100 p-6 dark:bg-gray-800">
          <Sparkles className="h-16 w-16 text-gray-400" />
        </div>
        <h2 className="mb-2 text-2xl font-semibold">No Memories Yet</h2>
        <p className="max-w-md text-center text-muted-foreground">
          Memories are generated automatically from your photos based on time and location.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col px-8 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Memories</h1>
        <p className="text-sm text-muted-foreground">
          Relive moments from your past
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {memories.map((memory) => (
          <Card
            key={memory.id}
            className="cursor-pointer transition hover:shadow-lg"
            onClick={() => handleMemoryClick(memory)}
          >
            <div className="relative aspect-video bg-muted">
              {memory.representative_image ? (
                <img
                  src={convertFileSrc(memory.representative_image.thumbnailPath)}
                  alt={memory.title}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <ImageIcon className="h-16 w-16 text-muted-foreground" />
                </div>
              )}
              <div className="absolute right-3 top-3">
                {getMemoryBadge(memory.memory_type)}
              </div>
            </div>

            <CardContent className="p-4">
              <div className="mb-2 flex justify-between">
                <h3 className="font-semibold line-clamp-1">{memory.title}</h3>
                {getMemoryIcon(memory.memory_type)}
              </div>

              <div className="mb-1 flex items-center gap-1 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                {formatDateRange(
                  memory.date_range_start,
                  memory.date_range_end,
                )}
              </div>

              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <ImageIcon className="h-4 w-4" />
                {memory.image_count} photos
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {isImageViewOpen && (
        <MediaView
          images={selectedMemoryImages}
          type="image"
        />
      )}
    </div>
  );
};

export default Memories;
