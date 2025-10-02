import { fetchAllImages } from '@/api/api-functions';
import { addImagesToAlbum } from '@/api/api-functions/albums';
import { RootState } from '@/app/store';
import { AddToAlbumDialog } from '@/components/Album/AddToAlbumDialog';
import { CreateAlbumDialog } from '@/components/Album/CreateAlbumDialog';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { SelectionToolbar } from '@/components/Media/SelectionToolbar';
import { Button } from '@/components/ui/button';
import {
  selectIsSelectionMode,
  selectSelectedImageIds,
} from '@/features/albumSelectors';
import {
  disableSelectionMode,
  enableSelectionMode,
} from '@/features/albumSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { setImages } from '@/features/imageSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import { Image } from '@/types/Media';
import { CheckSquare } from 'lucide-react';
import React from 'react';
import { useDispatch, useSelector } from 'react-redux';

export const Home = () => {
  const dispatch = useDispatch();
  const [showCreateAlbumDialog, setShowCreateAlbumDialog] =
    React.useState(false);
  const [showAddToAlbumDialog, setShowAddToAlbumDialog] = React.useState(false);

  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);
  const isSelectionMode = useSelector(selectIsSelectionMode);
  const selectedImageIds = useSelector(selectSelectedImageIds);

  // Mutation for adding images to album after creation
  const addImagesToAlbumMutation = usePictoMutation({
    mutationFn: ({
      albumId,
      imageIds,
    }: {
      albumId: string;
      imageIds: string[];
    }) => addImagesToAlbum(albumId, imageIds),
    onSuccess: () => {
      dispatch(disableSelectionMode());
      dispatch(
        showInfoDialog({
          title: 'Success',
          message: 'Album created and photos added successfully!',
          variant: 'info',
        }),
      );
    },
    onError: () => {
      dispatch(disableSelectionMode());
      dispatch(
        showInfoDialog({
          title: 'Warning',
          message:
            'Album was created but failed to add selected photos. You can add them manually.',
          variant: 'error',
        }),
      );
    },
  });

  const searchState = useSelector((state: RootState) => state.search);
  const isSearchActive = searchState.active;
  const searchResults = searchState.images;

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
    enabled: !isSearchActive,
  });

  // Handle fetching lifecycle
  React.useEffect(() => {
    if (!isSearchActive) {
      if (isLoading) {
        dispatch(showLoader('Loading images'));
      } else if (isError) {
        dispatch(hideLoader());
        dispatch(
          showInfoDialog({
            title: 'Error',
            message: 'Failed to load images. Please try again later.',
            variant: 'error',
          }),
        );
      } else if (isSuccess) {
        const images = data?.data as Image[];
        dispatch(setImages(images));
        dispatch(hideLoader());
      }
    }
  }, [data, isSuccess, isError, isLoading, dispatch, isSearchActive]);

  const handleCloseMediaView = () => {
    // MediaView will handle closing via Redux
  };

  const displayImages = isSearchActive ? searchResults : images;

  const handleEnterSelectionMode = () => {
    dispatch(enableSelectionMode());
  };

  const handleAddToAlbum = () => {
    setShowAddToAlbumDialog(true);
  };

  const handleCreateNewAlbum = () => {
    setShowCreateAlbumDialog(true);
  };

  const handleAlbumCreated = (albumId: string) => {
    console.log('Album created with ID:', albumId);

    // If there are selected images, add them to the newly created album
    if (selectedImageIds.length > 0) {
      addImagesToAlbumMutation.mutate({ albumId, imageIds: selectedImageIds });
    } else {
      // No images selected, just clear selection mode
      dispatch(disableSelectionMode());
    }
  };

  const handleImagesAddedToAlbum = () => {
    console.log('Images added to album');
    // Clear selection after adding to album
    dispatch(disableSelectionMode());
  };

  const title =
    isSearchActive && searchResults.length > 0
      ? `Face Search Results (${searchResults.length} found)`
      : 'Image Gallery';

  return (
    <div className="p-6">
      {/* Header with title and selection button */}
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{title}</h1>
        {!isSelectionMode && !isSearchActive && displayImages.length > 0 && (
          <Button
            onClick={handleEnterSelectionMode}
            variant="outline"
            className="gap-2"
          >
            <CheckSquare className="h-4 w-4" />
            Select Photos
          </Button>
        )}
      </div>

      {/* Image Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {displayImages.map((image: any, index: number) => (
          <ImageCard
            // @ts-expect-error - key is a special React prop not part of component props
            key={image.id}
            image={image}
            imageIndex={index}
            className="w-full"
          />
        ))}
      </div>

      {/* Selection Toolbar */}
      {isSelectionMode && (
        <SelectionToolbar
          onAddToAlbum={handleAddToAlbum}
          onCreateNewAlbum={handleCreateNewAlbum}
          onDownload={() => console.log('Download:', selectedImageIds)}
          onShare={() => console.log('Share:', selectedImageIds)}
          onDelete={() => console.log('Delete:', selectedImageIds)}
        />
      )}

      {/* Album Dialogs */}
      <CreateAlbumDialog
        open={showCreateAlbumDialog}
        onOpenChange={setShowCreateAlbumDialog}
        selectedImageIds={selectedImageIds}
        onAlbumCreated={handleAlbumCreated}
      />

      <AddToAlbumDialog
        open={showAddToAlbumDialog}
        onOpenChange={setShowAddToAlbumDialog}
        selectedImageIds={selectedImageIds}
        onImagesAdded={handleImagesAddedToAlbum}
      />

      {/* Media Viewer Modal */}
      {isImageViewOpen && (
        <MediaView images={displayImages} onClose={handleCloseMediaView} />
      )}
    </div>
  );
};
