/**
 * MemoryDetail Component
 *
 * Full page for viewing a memory's details and all photos.
 * Shows title, description, date, location, and a grid of all images.
 * Matches PersonImages page structure and styling.
 * Uses Tanstack Query for data fetching.
 */

import { useEffect, useMemo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useParams } from 'react-router';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { ROUTES } from '@/constants/routes';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import {
  setCurrentViewIndex,
  setImages,
  updateImageFavoriteStatus,
} from '@/features/imageSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import {
  useAllMemories,
  useRecentMemories,
  useYearMemories,
  useOnThisDay,
} from '@/hooks/useMemories';
import { type Memory } from '@/api/api-functions/memories';
import { formatDateRangeRelative } from '@/utils/memories';
import { togglefav } from '@/api/api-functions/togglefav';
import { useQueryClient } from '@tanstack/react-query';

export const MemoryDetail = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { memoryId } = useParams<{ memoryId: string }>();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);

  // Fetch data using Tanstack Query hooks
  const allMemoriesQuery = useAllMemories();
  const recentMemoriesQuery = useRecentMemories(30);
  const yearMemoriesQuery = useYearMemories(365);
  const onThisDayQuery = useOnThisDay();

  // Extract data
  const allMemories = (allMemoriesQuery.data?.data?.memories as any) || [];
  const recentMemories = (recentMemoriesQuery.data?.data?.memories as any) || [];
  const yearMemories = (yearMemoriesQuery.data?.data?.memories as any) || [];
  const onThisDayImages = (onThisDayQuery.data?.data?.images as any) || [];
  const onThisDayMeta = onThisDayQuery.data?.data
    ? {
        today: (onThisDayQuery.data.data as any).today,
        years: (onThisDayQuery.data.data as any).years,
      }
    : null;

  // Show error dialog if any query fails
  useEffect(() => {
    if (
      allMemoriesQuery.isError ||
      recentMemoriesQuery.isError ||
      yearMemoriesQuery.isError ||
      onThisDayQuery.isError
    ) {
      const errorMessage =
        allMemoriesQuery.errorMessage ||
        recentMemoriesQuery.errorMessage ||
        yearMemoriesQuery.errorMessage ||
        onThisDayQuery.errorMessage ||
        'Failed to load memory data';

      dispatch(
        showInfoDialog({
          title: 'Error Loading Memory',
          message: errorMessage,
          variant: 'error',
        }),
      );
    }
  }, [
    allMemoriesQuery.isError,
    allMemoriesQuery.errorMessage,
    recentMemoriesQuery.isError,
    recentMemoriesQuery.errorMessage,
    yearMemoriesQuery.isError,
    yearMemoriesQuery.errorMessage,
    onThisDayQuery.isError,
    onThisDayQuery.errorMessage,
    dispatch,
  ]);

  // Find memory from any source or create temp memory for "on-this-day"
  const memory = useMemo(() => {
    // Special case: "On This Day" - create temporary memory from images
    if (
      memoryId === 'on-this-day' &&
      onThisDayImages.length > 0 &&
      onThisDayMeta
    ) {
      const tempMemory: Memory = {
        memory_id: 'on-this-day',
        title: `On This Day - ${onThisDayMeta.today}`,
        description: `Photos from ${onThisDayMeta.years.join(', ')} years ago`,
        location_name: 'Various locations',
        date_start: onThisDayImages[0]?.captured_at || null,
        date_end:
          onThisDayImages[onThisDayImages.length - 1]?.captured_at || null,
        image_count: onThisDayImages.length,
        images: onThisDayImages,
        thumbnail_image_id: onThisDayImages[0]?.id || '',
        center_lat: onThisDayImages[0]?.latitude ?? null,
        center_lon: onThisDayImages[0]?.longitude ?? null,
      };
      return tempMemory;
    }

    // Search in all memory arrays
    return (
      allMemories.find((m: Memory) => m.memory_id === memoryId) ||
      recentMemories.find((m: Memory) => m.memory_id === memoryId) ||
      yearMemories.find((m: Memory) => m.memory_id === memoryId)
    );
  }, [
    memoryId,
    allMemories,
    recentMemories,
    yearMemories,
    onThisDayImages,
    onThisDayMeta,
  ]);

  // Handle favorite toggle - invalidate queries to refetch
  const handleToggleFavorite = useCallback(
    async (imageId: string) => {
      try {
        await togglefav(imageId);
        // Update Redux state for immediate UI feedback
        dispatch(updateImageFavoriteStatus(imageId));
        // Invalidate Tanstack Query cache to refetch memories
        queryClient.invalidateQueries({ queryKey: ['memories'] });
      } catch (error) {
        console.error('Failed to toggle favorite:', error);
        dispatch(
          showInfoDialog({
            title: 'Error',
            message: 'Failed to toggle favorite. Please try again.',
            variant: 'error',
          }),
        );
      }
    },
    [dispatch, queryClient],
  );

  // Load memory images into Redux state
  useEffect(() => {
    if (!memory) {
      dispatch(hideLoader());
      return;
    }

    dispatch(showLoader('Loading memory'));

    // Convert memory images to Image[] format for Redux state
    const formattedImages = memory.images.map((img: any) => ({
      id: img.id,
      path: img.path,
      thumbnailPath: img.thumbnailPath,
      folder_id: '',
      isTagged: false,
      isFavourite: img.isFavourite || false,
      tags: [],
      metadata: {
        name: img.path.split('/').pop() || '',
        date_created: img.captured_at,
        width: 0,
        height: 0,
        file_location: img.path,
        file_size: 0,
        item_type: 'image' as const,
        latitude: img.latitude ?? undefined,
        longitude: img.longitude ?? undefined,
      },
    }));

    // Defer setImages and hideLoader to next tick so loader becomes visible
    requestAnimationFrame(() => {
      dispatch(setImages(formattedImages));
      dispatch(hideLoader());
    });
  }, [memory, dispatch]);

  // If memory not found, show error
  if (!memory) {
    return (
      <div className="p-6">
        <Button
          variant="outline"
          onClick={() => navigate(`/${ROUTES.MEMORIES}`)}
          className="mb-6 flex cursor-pointer items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Memories
        </Button>
        <div className="border-border bg-muted/50 rounded-lg border-2 border-dashed p-12 text-center">
          <p className="text-muted-foreground text-lg">Memory not found</p>
        </div>
      </div>
    );
  }

  // Format title matching MemoryCard logic
  const isDateBased = memory.center_lat == null || memory.center_lon == null;
  let displayTitle = memory.title || 'Untitled Memory';
  const displayLocation = memory.location_name || '';

  // For location-based memories, format as "Trip to [Location], [Year]"
  if (!isDateBased && displayLocation) {
    const year = memory.date_start
      ? new Date(memory.date_start).getFullYear()
      : '';
    displayTitle = `Trip to ${displayLocation}${year ? `, ${year}` : ''}`;
  }

  return (
    <div className="flex h-full flex-col">
      {/* Fixed Header Section */}
      <div className="bg-background border-b px-6 py-3">
        {/* Back Button */}
        <div className="mb-3">
          <Button
            variant="outline"
            onClick={() => navigate(`/${ROUTES.MEMORIES}`)}
            className="flex cursor-pointer items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Memories
          </Button>
        </div>

        {/* Title with blue stripe and metadata inline - matching Home gallery style */}
        <div>
          <h1 className="flex items-center text-xl font-semibold text-gray-800 dark:text-gray-200">
            <div className="bg-primary mr-2 h-6 w-1"></div>
            {displayTitle}
            <div className="mt-1 ml-2 text-sm font-normal text-gray-500">
              {formatDateRangeRelative(memory.date_start, memory.date_end)}
              {displayLocation && (
                <>
                  {' • '}
                  {displayLocation}
                </>
              )}
            </div>
          </h1>
        </div>

        {/* Description */}
        {memory.description && (
          <p className="text-muted-foreground mt-2 ml-5 text-sm">
            {memory.description}
          </p>
        )}
      </div>

      {/* Scrollable Images Grid */}
      <div className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto px-6 py-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {images.map((image, index) => (
            <ImageCard
              key={image.id}
              image={image}
              imageIndex={index}
              className="w-full"
              onClick={() => dispatch(setCurrentViewIndex(index))}
            />
          ))}
        </div>
      </div>

      {/* MediaView for full-screen image viewing */}
      {isImageViewOpen && (
        <MediaView
          type="image"
          onToggleFavorite={handleToggleFavorite}
          images={images}
        />
      )}
    </div>
  );
};

export default MemoryDetail;
