import { DeleteAlbumDialog } from '@/components/Album/DeleteAlbumDialog';
import { EditAlbumDialog } from '@/components/Album/EditAlbumDialog';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { SelectionToolbar } from '@/components/Media/SelectionToolbar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import { ChangeEvent, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';

import {
  Album as AlbumType,
  fetchAlbum,
  fetchAlbumImages,
  removeImagesFromAlbum,
} from '@/api/api-functions/albums';
import { fetchAllImages } from '@/api/api-functions/images';
import {
  selectIsSelectionMode,
  selectSelectedImageIds,
} from '@/features/albumSelectors';
import {
  clearSelectedImages,
  enableSelectionMode,
  setSelectedAlbum,
} from '@/features/albumSlice';
import { selectIsImageViewOpen } from '@/features/imageSelectors';
import { setImages } from '@/features/imageSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Image } from '@/types/Media';
import {
  ArrowLeft,
  CheckSquare,
  Edit3,
  Lock,
  MoreHorizontal,
  Plus,
  Trash2,
} from 'lucide-react';

export function AlbumDetail() {
  const { albumId } = useParams<{ albumId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [album, setAlbum] = useState<AlbumType | null>(null);
  const [albumImages, setAlbumImages] = useState<Image[]>([]);
  const [password, setPassword] = useState('');
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const isSelectionMode = useSelector(selectIsSelectionMode);
  const selectedImageIds = useSelector(selectSelectedImageIds);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);

  // Mutation for removing images from album
  const removeImagesMutation = usePictoMutation({
    mutationFn: ({
      albumId,
      imageIds,
    }: {
      albumId: string;
      imageIds: string[];
    }) => removeImagesFromAlbum(albumId, imageIds),
    onSuccess: (data: any) => {
      if (data.success) {
        dispatch(
          showInfoDialog({
            title: 'Success',
            message: `Removed ${selectedImageIds.length} photo${
              selectedImageIds.length > 1 ? 's' : ''
            } from album`,
            variant: 'info',
          }),
        );

        // Update local state by filtering out removed images
        const updatedImages = albumImages.filter(
          (img) => !selectedImageIds.includes(img.id),
        );
        setAlbumImages(updatedImages);
        dispatch(setImages(updatedImages));

        // Clear selection
        dispatch(clearSelectedImages());
      }
    },
    onError: () => {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to remove photos from album. Please try again.',
          variant: 'error',
        }),
      );
    },
  });

  // Use mutation feedback for loading states
  useMutationFeedback(removeImagesMutation, {
    loadingMessage: 'Removing photos from album...',
    showSuccess: false, // We handle success manually
    errorTitle: 'Failed to Remove Photos',
  });

  // Fetch album details
  const {
    data: albumData,
    isLoading: isAlbumLoading,
    isSuccess: isAlbumSuccess,
    isError: isAlbumError,
  } = usePictoQuery({
    queryKey: ['album', albumId],
    queryFn: () =>
      albumId ? fetchAlbum(albumId) : Promise.reject('No album ID'),
    enabled: !!albumId,
  });

  // Fetch album images
  const {
    data: imageIdsData,
    isLoading: isImagesLoading,
    isSuccess: isImagesSuccess,
    isError: isImagesError,
  } = usePictoQuery({
    queryKey: ['album-images', albumId, password],
    queryFn: () =>
      albumId
        ? fetchAlbumImages(albumId, password || undefined)
        : Promise.reject('No album ID'),
    enabled: !!albumId && !!album && (!album.is_hidden || Boolean(password)),
  });

  // Fetch all images to get full image details
  const { data: allImagesData } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
  });

  // Handle loading states
  useEffect(() => {
    if (isAlbumLoading || isImagesLoading) {
      dispatch(showLoader('Loading album...'));
    } else {
      dispatch(hideLoader());
    }
  }, [isAlbumLoading, isImagesLoading, dispatch]);

  // Handle album data
  useEffect(() => {
    if (isAlbumSuccess && albumData?.success) {
      setAlbum(albumData.data);
      dispatch(setSelectedAlbum(albumData.data));

      // Check if album is hidden and we don't have password
      if (albumData.data.is_hidden && !password) {
        setShowPasswordDialog(true);
      }
    } else if (isAlbumError) {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to load album. Please try again.',
          variant: 'error',
        }),
      );
    }
  }, [isAlbumSuccess, isAlbumError, albumData, password, dispatch]);

  // Handle image IDs data
  useEffect(() => {
    if (isImagesSuccess && imageIdsData?.success && allImagesData?.data) {
      const imageIds = imageIdsData.image_ids;
      const allImagesArray = allImagesData.data as Image[];

      // Filter images that are in this album
      const filteredImages = allImagesArray.filter((image) =>
        imageIds.includes(image.id),
      );

      setAlbumImages(filteredImages);
      dispatch(setImages(filteredImages));
    }
  }, [isImagesSuccess, imageIdsData, allImagesData, dispatch]);

  // Handle failed password attempts for hidden albums
  useEffect(() => {
    // Check if query failed or returned unsuccessful response
    if (
      isImagesError ||
      (isImagesSuccess && imageIdsData && !imageIdsData.success)
    ) {
      // Only handle this for hidden albums with a password attempt
      if (album?.is_hidden && password) {
        // Clear the incorrect password
        setPassword('');

        // Clear any existing images from UI
        setAlbumImages([]);
        dispatch(setImages([]));

        // Show password dialog again for retry
        setShowPasswordDialog(true);

        // Show error notification
        dispatch(
          showInfoDialog({
            title: 'Invalid Password',
            message: 'The password you entered is incorrect. Please try again.',
            variant: 'error',
          }),
        );
      }
    }
  }, [isImagesError, isImagesSuccess, imageIdsData, album, password, dispatch]);

  const handleBack = () => {
    navigate('/albums');
  };

  const handleEnterSelectionMode = () => {
    dispatch(enableSelectionMode());
  };

  const handleEditAlbum = () => {
    setShowEditDialog(true);
  };

  const handleDeleteAlbum = () => {
    setShowDeleteDialog(true);
  };

  const handleAlbumUpdated = () => {
    // Album will be refetched via React Query
    console.log('Album updated successfully');
  };

  const handleAlbumDeleted = () => {
    // Navigate back to albums list after deletion
    navigate('/albums');
  };

  const handleRemoveFromAlbum = () => {
    if (!albumId || selectedImageIds.length === 0) return;

    removeImagesMutation.mutate({
      albumId,
      imageIds: selectedImageIds,
    });
  };

  const handlePasswordSubmit = (submittedPassword: string) => {
    setPassword(submittedPassword);
    setShowPasswordDialog(false);
  };

  const handleCloseMediaView = () => {
    // MediaView handles closing via Redux
  };

  if (!album) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <h2 className="mb-2 text-xl font-semibold">Loading...</h2>
          <p className="text-muted-foreground">
            Please wait while we load the album.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="mb-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBack}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Albums
          </Button>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex-1">
            <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
              <h1 className="text-2xl font-bold">{album.album_name}</h1>
              {album.is_hidden && (
                <Lock className="text-muted-foreground h-5 w-5" />
              )}
              <div className="flex gap-2">
                {album.is_hidden && <Badge variant="secondary">Hidden</Badge>}
                <Badge variant="outline">
                  {albumImages.length} photo
                  {albumImages.length !== 1 ? 's' : ''}
                </Badge>
              </div>
            </div>
            {album.description && (
              <p className="text-muted-foreground">{album.description}</p>
            )}
          </div>

          <div className="flex flex-shrink-0 items-center gap-2">
            {!isSelectionMode && albumImages.length > 0 && (
              <Button
                onClick={handleEnterSelectionMode}
                variant="outline"
                className="gap-2"
              >
                <CheckSquare className="h-4 w-4" />
                Select Photos
              </Button>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  <MoreHorizontal className="h-4 w-4" />
                  Options
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleEditAlbum}>
                  <Edit3 className="mr-2 h-4 w-4" />
                  Edit Album
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={handleDeleteAlbum}
                  className="text-red-600"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Album
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Empty state */}
      {albumImages.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="text-center">
            <h2 className="mb-2 text-xl font-semibold">
              No photos in this album
            </h2>
            <p className="text-muted-foreground mb-4">
              Add photos to this album from your photo collection.
            </p>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Add Photos
            </Button>
          </div>
        </div>
      ) : (
        /* Image Grid */
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {albumImages.map((image: any, index: number) => (
            <ImageCard
              key={image.id}
              image={image}
              imageIndex={index}
              className="w-full"
            />
          ))}
        </div>
      )}

      {/* Selection Toolbar */}
      {isSelectionMode && (
        <SelectionToolbar
          onDownload={() => console.log('Download:', selectedImageIds)}
          onShare={() => console.log('Share:', selectedImageIds)}
          onRemoveFromAlbum={handleRemoveFromAlbum}
          showAlbumActions={false}
          showRemoveFromAlbum={true}
        />
      )}

      {/* Media Viewer Modal */}
      {isImageViewOpen && (
        <MediaView images={albumImages} onClose={handleCloseMediaView} />
      )}

      {/* Password Dialog for Hidden Albums */}
      <PasswordDialog
        open={showPasswordDialog}
        onOpenChange={setShowPasswordDialog}
        onPasswordSubmit={handlePasswordSubmit}
        albumName={album?.album_name || 'Album'}
      />

      {/* Edit Album Dialog */}
      {albumId && (
        <EditAlbumDialog
          open={showEditDialog}
          onOpenChange={setShowEditDialog}
          albumId={albumId}
          onAlbumUpdated={handleAlbumUpdated}
        />
      )}

      {/* Delete Album Dialog */}
      {albumId && album && (
        <DeleteAlbumDialog
          open={showDeleteDialog}
          onOpenChange={setShowDeleteDialog}
          albumId={albumId}
          albumName={album.album_name}
          onAlbumDeleted={handleAlbumDeleted}
        />
      )}
    </div>
  );
}

// Password Dialog Component
interface PasswordDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPasswordSubmit: (password: string) => void;
  albumName: string;
}

function PasswordDialog({
  open,
  onOpenChange,
  onPasswordSubmit,
  albumName,
}: PasswordDialogProps) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: any) => {
    e.preventDefault();
    if (!password.trim()) {
      setError('Password is required');
      return;
    }
    onPasswordSubmit(password);
    setPassword('');
    setError('');
  };

  const handleCancel = () => {
    setPassword('');
    setError('');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Enter Album Password</DialogTitle>
          <DialogDescription>
            This album is password protected. Please enter the password to view
            "{albumName}".
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="album-password">Password</Label>
            <Input
              id="album-password"
              type="password"
              placeholder="Enter album password"
              value={password}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setPassword(e.target.value)
              }
              className={error ? 'border-red-500' : ''}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button type="submit">Access Album</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
