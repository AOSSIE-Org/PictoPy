/**
 * MemoryDetail Component
 *
 * Full page for viewing a memory's details and all photos.
 * Shows title, description, date, location, and a grid of all images.
 * Matches PersonImages page structure and styling.
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
import { useAppSelector } from '@/store/hooks';
import {
  selectAllMemories,
  selectRecentMemories,
  selectYearMemories,
  selectOnThisDayImages,
  selectOnThisDayMeta,
} from '@/store/slices/memoriesSlice';
import { formatDateRangeRelative, type Memory } from '@/services/memoriesApi';
import { togglefav } from '@/api/api-functions/togglefav';

export const MemoryDetail = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { memoryId } = useParams<{ memoryId: string }>();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);

  // Get memories from all possible sources
  const allMemories = useAppSelector(selectAllMemories);
  const recentMemories = useAppSelector(selectRecentMemories);
  const yearMemories = useAppSelector(selectYearMemories);
  const onThisDayImages = useAppSelector(selectOnThisDayImages);
  const onThisDayMeta = useAppSelector(selectOnThisDayMeta);

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
      allMemories.find((m) => m.memory_id === memoryId) ||
      recentMemories.find((m) => m.memory_id === memoryId) ||
      yearMemories.find((m) => m.memory_id === memoryId)
    );
  }, [
    memoryId,
    allMemories,
    recentMemories,
    yearMemories,
    onThisDayImages,
    onThisDayMeta,
  ]);

  // Handle favorite toggle with Redux state update
  const handleToggleFavorite = useCallback(
    async (imageId: string) => {
      try {
        await togglefav(imageId);
        // Update Redux state to reflect the change immediately
        dispatch(updateImageFavoriteStatus(imageId));
      } catch (error) {
        console.error('Failed to toggle favorite:', error);
      }
    },
    [dispatch],
  );

  // Load memory images into Redux state
  useEffect(() => {
    if (!memory) {
      dispatch(hideLoader());
      return;
    }

    dispatch(showLoader('Loading memory'));

    // Convert memory images to Image[] format for Redux state
    const formattedImages = memory.images.map((img) => ({
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
