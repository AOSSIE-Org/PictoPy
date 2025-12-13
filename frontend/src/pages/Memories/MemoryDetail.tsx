import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { ArrowLeft, Calendar, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchMemoryImages } from '@/api/api-functions';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { useDispatch } from 'react-redux';
import { ChronologicalGallery } from '@/components/Media/ChronologicalGallery';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export const MemoryDetail = () => {
  const { memoryId } = useParams<{ memoryId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [memoryImages, setMemoryImages] = useState<Image[]>([]);
  const [memoryTitle, setMemoryTitle] = useState<string>('');
  const [memoryInfo, setMemoryInfo] = useState<any>(null);

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['memory-images', memoryId],
    queryFn: () => fetchMemoryImages({ memoryId: memoryId || '' }),
    enabled: !!memoryId,
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading memory',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load memory. Please try again later.',
    },
  );

  useEffect(() => {
    if (isSuccess && data?.data) {
      const memoryData = data.data as any;
      const images = memoryData.images.map((img: any) => ({
        id: img.id,
        path: img.path,
        thumbnailPath: img.thumbnailPath,
        folder_id: '',
        isTagged: false,
        metadata: img.metadata,
      }));

      setMemoryImages(images);
      setMemoryTitle(memoryData.memory.title);
      setMemoryInfo(memoryData.memory);
      dispatch(setImages(images));
    }
  }, [isSuccess, data, dispatch]);

  const handleBack = () => {
    navigate('/memories');
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

  return (
    <div className="flex h-full flex-col px-8 py-6">
      <div className="mb-6">
        <Button
          onClick={handleBack}
          variant="ghost"
          className="mb-4 flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Memories
        </Button>

        <h1 className="mb-2 text-2xl font-bold">{memoryTitle}</h1>

        {memoryInfo && (
          <div className="text-muted-foreground flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>
                {formatDateRange(
                  memoryInfo.date_range_start,
                  memoryInfo.date_range_end,
                )}
              </span>
            </div>

            {memoryInfo.location_name && (
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                <span>{memoryInfo.location_name}</span>
              </div>
            )}

            <span>{memoryInfo.image_count} photos</span>
          </div>
        )}
      </div>

      <div className="hide-scrollbar flex-1 overflow-y-auto">
        {memoryImages.length > 0 && (
          <ChronologicalGallery
            images={memoryImages}
          />
        )}
      </div>
    </div>
  );
};

export default MemoryDetail;
