import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { Calendar, MapPin, Image as ImageIcon, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllMemories, generateMemories } from '@/api/api-functions';
import { Memory } from '@/types/Media';
import { Badge } from '@/components/ui/badge';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { usePictoMutation } from '@/hooks/useQueryExtension';

const Memories = () => {
  const navigate = useNavigate();
  const [memories, setMemories] = useState<Memory[]>([]);

  const {
    data: memoriesData,
    isLoading,
    isSuccess,
    isError,
    error,
    refetch,
  } = usePictoQuery({
    queryKey: ['memories'],
    queryFn: fetchAllMemories,
  });

  const generateMemoriesMutation = usePictoMutation({
    mutationFn: generateMemories,
    onSuccess: () => {
      refetch();
    },
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

  useMutationFeedback(
    {
      isPending: generateMemoriesMutation.isPending,
      isSuccess: generateMemoriesMutation.isSuccess,
      isError: generateMemoriesMutation.isError,
      error: generateMemoriesMutation.error,
    },
    {
      loadingMessage: 'Generating memories',
      successMessage: 'Memories generated successfully!',
      errorTitle: 'Error',
      errorMessage: 'Failed to generate memories.',
    },
  );

  useEffect(() => {
    if (isSuccess && memoriesData?.data) {
      setMemories(memoriesData.data as Memory[]);
    }
  }, [isSuccess, memoriesData]);

  const handleMemoryClick = (memoryId: string) => {
    // Navigate to memory detail page with images
    navigate(`/memories/${memoryId}`);
  };

  const handleGenerateMemories = () => {
    generateMemoriesMutation.mutate();
  };

  const formatDateRange = (start: string, end: string) => {
    const startDate = new Date(start);
    const endDate = new Date(end);

    if (startDate.toDateString() === endDate.toDateString()) {
      return startDate.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      });
    }

    return `${startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
  };

  const getMemoryIcon = (type: string) => {
    switch (type) {
      case 'on_this_day':
        return <Calendar className="h-5 w-5" />;
      case 'trip':
        return <MapPin className="h-5 w-5" />;
      default:
        return <ImageIcon className="h-5 w-5" />;
    }
  };

  const getMemoryBadge = (type: string) => {
    switch (type) {
      case 'on_this_day':
        return (
          <Badge variant="secondary" className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            On This Day
          </Badge>
        );
      case 'trip':
        return (
          <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
            Trip
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary">
            Memory
          </Badge>
        );
    }
  };

  if (memories.length === 0 && !isLoading) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8">
        <div className="mb-6 rounded-full bg-gray-100 p-6 dark:bg-gray-800">
          <Sparkles className="h-16 w-16 text-gray-400" strokeWidth={1.5} />
        </div>
        <h2 className="mb-2 text-2xl font-semibold text-gray-700 dark:text-gray-300">
          No Memories Yet
        </h2>
        <p className="mb-6 max-w-md text-center text-gray-500 dark:text-gray-400">
          Memories will be automatically created based on your photos' dates and
          locations. Generate memories to see them here.
        </p>
        <Button
          onClick={handleGenerateMemories}
          disabled={generateMemoriesMutation.isPending}
          className="flex items-center gap-2"
        >
          <Sparkles className="h-4 w-4" />
          {generateMemoriesMutation.isPending
            ? 'Generating...'
            : 'Generate Memories'}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col px-8 py-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Memories</h1>
          <p className="text-muted-foreground text-sm">
            Relive your special moments from the past
          </p>
        </div>
        <Button
          onClick={handleGenerateMemories}
          disabled={generateMemoriesMutation.isPending}
          variant="outline"
          className="flex items-center gap-2"
        >
          <Sparkles className="h-4 w-4" />
          {generateMemoriesMutation.isPending
            ? 'Generating...'
            : 'Regenerate'}
        </Button>
      </div>

      <div className="hide-scrollbar flex-1 overflow-y-auto">
        <div className="grid grid-cols-1 gap-4 pb-6 md:grid-cols-2 lg:grid-cols-3">
          {memories.map((memory) => (
            <Card
              key={memory.memory_id}
              className="group cursor-pointer overflow-hidden transition-all hover:shadow-lg"
              onClick={() => handleMemoryClick(memory.memory_id)}
            >
              <div className="relative aspect-video overflow-hidden bg-gray-100 dark:bg-gray-800">
                {memory.representative_image ? (
                  <img
                    src={`file://${memory.representative_image.thumbnailPath}`}
                    alt={memory.title}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <ImageIcon className="h-16 w-16 text-gray-400" />
                  </div>
                )}
                <div className="absolute top-3 right-3">
                  {getMemoryBadge(memory.memory_type)}
                </div>
              </div>

              <CardContent className="p-4">
                <div className="mb-2 flex items-start justify-between">
                  <h3 className="font-semibold text-lg line-clamp-1">
                    {memory.title}
                  </h3>
                  <div className="text-muted-foreground ml-2 flex-shrink-0">
                    {getMemoryIcon(memory.memory_type)}
                  </div>
                </div>

                <div className="text-muted-foreground mb-2 flex items-center gap-1 text-sm">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDateRange(memory.date_range_start, memory.date_range_end)}</span>
                </div>

                {memory.location_name && (
                  <div className="text-muted-foreground mb-2 flex items-center gap-1 text-sm">
                    <MapPin className="h-4 w-4" />
                    <span className="line-clamp-1">{memory.location_name}</span>
                  </div>
                )}

                <div className="text-muted-foreground flex items-center gap-1 text-sm">
                  <ImageIcon className="h-4 w-4" />
                  <span>{memory.image_count} {memory.image_count === 1 ? 'photo' : 'photos'}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Memories;
