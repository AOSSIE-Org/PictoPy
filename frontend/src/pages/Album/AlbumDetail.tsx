import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate, useLocation } from 'react-router';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Plus, Trash2, ImageIcon } from 'lucide-react';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { AddImagesToAlbumDialog } from '@/components/Albums/AddImagesToAlbumDialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import {
  getAlbumById,
  getAlbumImages,
  removeMultipleImagesFromAlbum,
  fetchAllImages,
  setAlbumCoverImage,
} from '@/api/api-functions';
import {
  setSelectedAlbum,
  setAlbumImages,
  clearAlbumImages,
} from '@/features/albumsSlice';
import {
  setCurrentViewIndex,
  setImages,
  clearImages,
} from '@/features/imageSlice';
import {
  selectSelectedAlbum,
  selectAlbumImages,
} from '@/features/albumSelectors';
import { selectIsImageViewOpen } from '@/features/imageSelectors';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { Album } from '@/types/Album';
import { Image } from '@/types/Media';

export const AlbumDetail = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { albumId } = useParams<{ albumId: string }>();

  const album = useSelector(selectSelectedAlbum);
  const images = useSelector(selectAlbumImages);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);

  const [isAddImagesDialogOpen, setIsAddImagesDialogOpen] = useState(false);
  const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [contextMenuImage, setContextMenuImage] = useState<number | null>(null);

  // Get password from navigation state if album is locked
  const password = location.state?.password;

  const {
    data: albumData,
    isLoading: isLoadingAlbum,
    refetch: refetchAlbum,
  } = usePictoQuery({
    queryKey: ['album', albumId],
    queryFn: () => getAlbumById(albumId!),
    enabled: !!albumId,
  });

  const {
    data: imagesData,
    isLoading: isLoadingImages,
    isSuccess: imagesSuccess,
    isError: imagesError,
    refetch: refetchImages,
  } = usePictoQuery({
    queryKey: ['album-images', albumId],
    queryFn: () =>
      getAlbumImages(albumId!, password ? { password } : undefined),
    enabled: !!albumId && !!album,
  });

  // Fetch all images to get full details
  const { data: allImagesData } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
    enabled: !!albumId && !!album,
  });

  const { mutate: removeImagesMutate } = usePictoMutation({
    mutationFn: ({
      albumId,
      imageIds,
    }: {
      albumId: string;
      imageIds: string[];
    }) => removeMultipleImagesFromAlbum(albumId, { image_ids: imageIds }),
    onSuccess: () => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Success',
          message: 'Images removed from album successfully!',
          variant: 'info',
        }),
      );
      setSelectedImages(new Set());
      setIsSelectionMode(false);
      refetchImages();
    },
    onError: (error: any) => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Error',
          message:
            error?.message || 'Failed to remove images. Please try again.',
          variant: 'error',
        }),
      );
    },
  });

  const { mutate: setCoverImageMutate } = usePictoMutation({
    mutationFn: ({ albumId, imageId }: { albumId: string; imageId: string }) =>
      setAlbumCoverImage(albumId, imageId),
    onSuccess: () => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Success',
          message: 'Album cover image updated successfully!',
          variant: 'info',
        }),
      );
      // Refetch album data to get updated cover image
      refetchAlbum();
    },
    onError: (error: any) => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Error',
          message:
            error?.message || 'Failed to set cover image. Please try again.',
          variant: 'error',
        }),
      );
    },
  });

  useEffect(() => {
    if (albumData) {
      // Backend returns album data with album_id, album_name format
      const responseData = albumData.data as any;
      const backendAlbum = (responseData?.album || responseData) as any;

      if (backendAlbum && backendAlbum.album_id) {
        // Transform backend format to frontend format
        const albumInfo: Album = {
          id: backendAlbum.album_id,
          name: backendAlbum.album_name,
          description: backendAlbum.description || '',
          is_locked: backendAlbum.is_locked || false,
          cover_image_path: backendAlbum.cover_image_path,
          image_count: backendAlbum.image_count || 0,
          created_at: backendAlbum.created_at || new Date().toISOString(),
          updated_at: backendAlbum.updated_at || new Date().toISOString(),
        };
        dispatch(setSelectedAlbum(albumInfo));
      }
    }
  }, [albumData, dispatch]);

  useEffect(() => {
    if (isLoadingImages) {
      dispatch(showLoader('Loading album images...'));
    } else if (imagesError) {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Error',
          message:
            'Failed to load album images. Please check your password and try again.',
          variant: 'error',
        }),
      );
      navigate('/albums');
    } else if (imagesSuccess && imagesData && allImagesData) {
      // Backend returns {"success":true,"image_ids":[...]} structure
      const responseData = imagesData as any;
      const imageIds = (responseData?.image_ids || []) as string[];

      // Get full image data from all images
      const allImages = (allImagesData?.data || []) as Image[];

      // Filter images that are in this album
      const albumImages = allImages.filter((img) => imageIds.includes(img.id));

      dispatch(setAlbumImages(albumImages));
      dispatch(setImages(albumImages));
      dispatch(hideLoader());
    }
  }, [
    imagesData,
    allImagesData,
    imagesSuccess,
    imagesError,
    isLoadingImages,
    dispatch,
    navigate,
  ]);

  useEffect(() => {
    return () => {
      dispatch(clearAlbumImages());
      dispatch(clearImages());
      dispatch(setSelectedAlbum(null));
    };
  }, [dispatch]);

  const handleImageClick = (index: number) => {
    if (isSelectionMode) {
      const imageId = images[index].id;
      const newSelected = new Set(selectedImages);
      if (newSelected.has(imageId)) {
        newSelected.delete(imageId);
      } else {
        newSelected.add(imageId);
      }
      setSelectedImages(newSelected);
    } else {
      dispatch(setCurrentViewIndex(index));
    }
  };

  const handleRemoveSelected = () => {
    if (selectedImages.size === 0) return;

    dispatch(showLoader('Removing images from album...'));
    removeImagesMutate({
      albumId: albumId!,
      imageIds: Array.from(selectedImages),
    });
  };

  const handleSetCoverImage = (imageId: string) => {
    dispatch(showLoader('Setting album cover...'));
    setCoverImageMutate({
      albumId: albumId!,
      imageId: imageId,
    });
  };

  const handleBack = () => {
    navigate('/albums');
  };

  if (isLoadingAlbum) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Loading album...</p>
      </div>
    );
  }

  if (!album) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Album not found</p>
          <Button onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Albums
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="mb-6">
        <div className="mb-4 flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">{album.name}</h1>
            {album.description && (
              <p className="text-muted-foreground text-sm">
                {album.description}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-muted-foreground text-sm">
            {images.length} {images.length === 1 ? 'photo' : 'photos'}
            {selectedImages.size > 0 && ` • ${selectedImages.size} selected`}
          </p>

          <div className="flex items-center gap-2">
            {isSelectionMode ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsSelectionMode(false);
                    setSelectedImages(new Set());
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleRemoveSelected}
                  disabled={selectedImages.size === 0}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Remove Selected
                </Button>
              </>
            ) : (
              <>
                {images.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsSelectionMode(true)}
                  >
                    Select Images
                  </Button>
                )}
                <Button
                  size="sm"
                  onClick={() => setIsAddImagesDialogOpen(true)}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Images
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Images Grid */}
      <div className="flex-1 overflow-y-auto pt-2">
        {images.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <p className="text-muted-foreground mb-4">
                No images in this album yet
              </p>
              <Button onClick={() => setIsAddImagesDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Images
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 pb-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
            {images.map((image, index) => (
              <div key={image.id} className="relative">
                <DropdownMenu
                  open={contextMenuImage === index}
                  onOpenChange={(open) => {
                    if (!open) setContextMenuImage(null);
                  }}
                >
                  <DropdownMenuTrigger asChild>
                    <div
                      className="cursor-pointer"
                      onClick={() => handleImageClick(index)}
                      onContextMenu={(e) => {
                        e.preventDefault();
                        if (!isSelectionMode) {
                          setContextMenuImage(index);
                        }
                      }}
                    >
                      <ImageCard
                        image={image}
                        className={
                          isSelectionMode && selectedImages.has(image.id)
                            ? 'ring-primary ring-2 ring-offset-2'
                            : ''
                        }
                      />
                      {isSelectionMode && selectedImages.has(image.id) && (
                        <div className="bg-primary text-primary-foreground absolute top-2 right-2 flex h-6 w-6 items-center justify-center rounded-full">
                          ✓
                        </div>
                      )}
                    </div>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSetCoverImage(image.id);
                        setContextMenuImage(null);
                      }}
                    >
                      <ImageIcon className="mr-2 h-4 w-4" />
                      Set as Cover
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Media View */}
      {isImageViewOpen && <MediaView images={images} />}

      {/* Add Images Dialog */}
      <AddImagesToAlbumDialog
        isOpen={isAddImagesDialogOpen}
        onClose={() => {
          setIsAddImagesDialogOpen(false);
          refetchImages();
        }}
        albumId={albumId!}
        albumName={album.name}
      />
    </div>
  );
};

export default AlbumDetail;
