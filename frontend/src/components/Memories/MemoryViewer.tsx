/**
 * MemoryViewer Component
 *
 * Full-screen modal for viewing a memory's details and all photos.
 * Shows title, description, date, location, and a grid of all images.
 * When an image is clicked, opens MediaView for full slideshow/zoom experience.
 */

import React, { useEffect, useCallback, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  selectSelectedMemory,
  clearSelectedMemory,
} from '@/features/memoriesSlice';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { MediaView } from '@/components/Media/MediaView';
import {
  formatDateRangeRelative,
  formatPhotoCount,
  getThumbnailUrl,
  generateMemoryTitle,
  formatLocationName,
} from '@/utils/memories';
import { togglefav } from '@/api/api-functions/togglefav';
import { getErrorMessage } from '@/lib/utils';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Memory Viewer Modal Component
 */
export const MemoryViewer: React.FC = () => {
  const dispatch = useAppDispatch();
  const queryClient = useQueryClient();
  const memory = useAppSelector(selectSelectedMemory);
  const [showMediaView, setShowMediaView] = useState(false);

  // Handle close memory viewer
  const handleCloseViewer = useCallback(() => {
    dispatch(clearSelectedMemory());
  }, [dispatch]);

  // Handle favorite toggle - update API and invalidate cache
  const handleToggleFavorite = useCallback(
    async (imageId: string) => {
      try {
        // Call API to toggle favorite in database
        await togglefav(imageId);

        // Invalidate all memories queries to refetch updated data
        queryClient.invalidateQueries({ queryKey: ['memories'] });
      } catch (error) {
        // Show error dialog to user
        dispatch(
          showInfoDialog({
            title: 'Failed to Update Favorite',
            message: getErrorMessage(error),
            variant: 'error',
          }),
        );
        console.error('Failed to toggle favorite:', error);
      }
    },
    [dispatch, queryClient],
  );

  // Handle image click - open MediaView
  const handleImageClick = useCallback(
    (index: number) => {
      if (!memory) return;

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
          latitude: img.latitude || undefined,
          longitude: img.longitude || undefined,
        },
      }));

      // Set images in Redux state first
      dispatch(setImages(formattedImages));
      // Then set the current index
      dispatch(setCurrentViewIndex(index));
      setShowMediaView(true);
    },
    [memory, dispatch],
  );

  // Handle MediaView close - go back to memory grid
  const handleMediaViewClose = useCallback(() => {
    setShowMediaView(false);
    dispatch(setCurrentViewIndex(-1)); // Reset view index
  }, [dispatch]);

  // Handle ESC key press
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleCloseViewer();
      }
    };

    if (memory) {
      document.addEventListener('keydown', handleEsc);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [memory, handleCloseViewer]);

  // Don't render if no memory selected
  if (!memory) return null;

  // Generate better title and format location
  const displayTitle = generateMemoryTitle(memory);
  const displayLocation = formatLocationName(memory.location_name);

  // Handle image load error
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.src = '/photo.png';
  };

  return (
    <>
      {/* Memory Grid Modal - hide when MediaView is open */}
      {!showMediaView && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm"
          onClick={handleCloseViewer}
          role="dialog"
          aria-modal="true"
          aria-labelledby="memory-viewer-title"
        >
          {/* Modal Container */}
          <div className="min-h-screen px-4 py-8">
            <div
              className="relative mx-auto max-w-7xl rounded-xl bg-white shadow-2xl dark:bg-gray-900"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="sticky top-0 z-10 rounded-t-xl border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
                <div className="flex items-center justify-between p-6">
                  <div className="min-w-0 flex-1 pr-4">
                    {/* Title */}
                    <h2
                      id="memory-viewer-title"
                      className="truncate text-2xl font-bold text-gray-900 md:text-3xl dark:text-white"
                    >
                      {displayTitle}
                    </h2>

                    {/* Metadata */}
                    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600 dark:text-gray-400">
                      {/* Date Range - Relative */}
                      <div className="flex items-center">
                        <svg
                          className="mr-1.5 h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        <span>
                          {formatDateRangeRelative(
                            memory.date_start,
                            memory.date_end,
                          )}
                        </span>
                      </div>

                      {/* Location - Only show if not coordinates */}
                      {displayLocation && (
                        <div className="flex items-center">
                          <svg
                            className="mr-1.5 h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                          </svg>
                          <span className="truncate">{displayLocation}</span>
                        </div>
                      )}

                      {/* Photo Count */}
                      <div className="flex items-center">
                        <svg
                          className="mr-1.5 h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        <span>{formatPhotoCount(memory.image_count)}</span>
                      </div>
                    </div>

                    {/* Description */}
                    {memory.description && (
                      <p className="mt-3 line-clamp-2 text-sm text-gray-600 dark:text-gray-400">
                        {memory.description}
                      </p>
                    )}
                  </div>

                  {/* Close Button */}
                  <button
                    onClick={handleCloseViewer}
                    className="shrink-0 rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-200"
                    aria-label="Close memory viewer"
                  >
                    <svg
                      className="h-6 w-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Images Grid */}
              <div className="p-6">
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 md:gap-4 lg:grid-cols-5">
                  {memory.images.map((image, index) => (
                    <div
                      key={image.id}
                      className="group relative aspect-square cursor-pointer overflow-hidden rounded-lg bg-gray-200 transition-all hover:ring-2 hover:ring-blue-500 dark:bg-gray-800"
                      onClick={() => handleImageClick(index)}
                    >
                      <img
                        src={getThumbnailUrl(image)}
                        alt={`Photo ${image.id}`}
                        onError={handleImageError}
                        className="h-full w-full object-cover transition-transform duration-200 group-hover:scale-110"
                        loading="lazy"
                      />

                      {/* Hover Overlay */}
                      <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors group-hover:bg-black/20">
                        <svg
                          className="h-8 w-8 text-white opacity-0 transition-opacity group-hover:opacity-100"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
                          />
                        </svg>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Footer (optional - for future features like share, download, etc.) */}
              <div className="rounded-b-xl border-t border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-800 dark:bg-gray-800/50">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Click any photo to view with zoom and slideshow
                  </p>

                  {/* Future: Add share, download buttons here */}
                  <div className="flex items-center space-x-2">
                    {/* Placeholder for future actions */}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MediaView for full-screen image viewing with zoom/slideshow */}
      {showMediaView && memory && (
        <MediaView
          onClose={handleMediaViewClose}
          type="image"
          onToggleFavorite={handleToggleFavorite}
          images={memory.images.map((img) => ({
            id: img.id,
            path: img.path,
            thumbnailPath: img.thumbnailPath,
            folder_id: '', // Memory images don't have folder_id
            isTagged: false, // Memory images don't track tagging
            isFavourite: img.isFavourite || false, // Use actual favorite status from backend
            tags: [], // Can be added later if needed
            metadata: {
              name: img.path.split('/').pop() || '',
              date_created: img.captured_at,
              width: 0,
              height: 0,
              file_location: img.path,
              file_size: 0,
              item_type: 'image',
              latitude: img.latitude || undefined,
              longitude: img.longitude || undefined,
            },
          }))}
        />
      )}
    </>
  );
};

export default MemoryViewer;
