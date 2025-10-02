import * as React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { SelectionToolbar } from '@/components/Media/SelectionToolbar';
import { usePictoQuery } from '@/hooks/useQueryExtension';

import { 
  fetchAlbum, 
  fetchAlbumImages,
  Album as AlbumType,
} from '@/api/api-functions/albums';
import { fetchAllImages } from '@/api/api-functions/images';
import {
  selectIsSelectionMode,
  selectSelectedImageIds,
} from '@/features/albumSelectors';
import { selectIsImageViewOpen } from '@/features/imageSelectors';
import { 
  enableSelectionMode, 
  setSelectedAlbum,
} from '@/features/albumSlice';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import {
  ArrowLeft,
  Trash2,
  Plus,
  MoreHorizontal,
  Lock,
  Edit3,
  CheckSquare,
} from 'lucide-react';
import { Image } from '@/types/Media';

export function AlbumDetail() {
  const { albumId } = useParams<{ albumId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  const [album, setAlbum] = React.useState<AlbumType | null>(null);
  const [albumImages, setAlbumImages] = React.useState<Image[]>([]);
  const [password] = React.useState('');
  const [, setShowPasswordDialog] = React.useState(false);

  const isSelectionMode = useSelector(selectIsSelectionMode);
  const selectedImageIds = useSelector(selectSelectedImageIds);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);


  // Fetch album details
  const { 
    data: albumData, 
    isLoading: isAlbumLoading, 
    isSuccess: isAlbumSuccess,
    isError: isAlbumError,
  } = usePictoQuery({
    queryKey: ['album', albumId],
    queryFn: () => albumId ? fetchAlbum(albumId) : Promise.reject('No album ID'),
    enabled: !!albumId,
  });

  // Fetch album images
  const { 
    data: imageIdsData, 
    isLoading: isImagesLoading,
    isSuccess: isImagesSuccess,

  } = usePictoQuery({
    queryKey: ['album-images', albumId, password],
    queryFn: () => albumId ? fetchAlbumImages(albumId, password || undefined) : Promise.reject('No album ID'),
    enabled: !!albumId && !!album && (!album.is_hidden || !!password),
  });

  // Fetch all images to get full image details
  const { data: allImagesData } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
  });

  // Handle loading states
  React.useEffect(() => {
    if (isAlbumLoading || isImagesLoading) {
      dispatch(showLoader('Loading album...'));
    } else {
      dispatch(hideLoader());
    }
  }, [isAlbumLoading, isImagesLoading, dispatch]);

  // Handle album data
  React.useEffect(() => {
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
  React.useEffect(() => {
    if (isImagesSuccess && imageIdsData?.success && allImagesData?.data) {
      const imageIds = imageIdsData.image_ids;
      const allImagesArray = allImagesData.data as Image[];
      
      // Filter images that are in this album
      const filteredImages = allImagesArray.filter(image => 
        imageIds.includes(image.id)
      );
      
      setAlbumImages(filteredImages);
      dispatch(setImages(filteredImages));
    }
  }, [isImagesSuccess, imageIdsData, allImagesData, dispatch]);

  const handleBack = () => {
    navigate('/albums');
  };

  const handleEnterSelectionMode = () => {
    dispatch(enableSelectionMode());
  };

  const handleEditAlbum = () => {
    // TODO: Implement edit album dialog
    console.log('Edit album:', albumId);
  };

  const handleDeleteAlbum = () => {
    // TODO: Implement delete album confirmation
    console.log('Delete album:', albumId);
  };

  const handleRemoveFromAlbum = () => {
    // TODO: Implement remove images from album
    console.log('Remove from album:', selectedImageIds);
  };

  

  const handleCloseMediaView = () => {
    // MediaView handles closing via Redux
  };

  if (!album) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Loading...</h2>
          <p className="text-muted-foreground">Please wait while we load the album.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <Button variant="ghost" size="sm" onClick={handleBack} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Albums
          </Button>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex-1">
            <div className="flex flex-col gap-2 mb-2 sm:flex-row sm:items-center sm:gap-3">
              <h1 className="text-2xl font-bold">{album.album_name}</h1>
              {album.is_hidden && (
                <Lock className="h-5 w-5 text-muted-foreground" />
              )}
              <div className="flex gap-2">
                {album.is_hidden && (
                  <Badge variant="secondary">Hidden</Badge>
                )}
                <Badge variant="outline">
                  {albumImages.length} photo{albumImages.length !== 1 ? 's' : ''}
                </Badge>
              </div>
            </div>
            {album.description && (
              <p className="text-muted-foreground">{album.description}</p>
            )}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
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
                  <Edit3 className="h-4 w-4 mr-2" />
                  Edit Album
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={handleDeleteAlbum}
                  className="text-red-600"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
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
            <h2 className="text-xl font-semibold mb-2">No photos in this album</h2>
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

      {/* TODO: Add password dialog for hidden albums */}
    </div>
  );
}