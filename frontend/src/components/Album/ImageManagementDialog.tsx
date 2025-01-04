import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { convertFileSrc } from '@tauri-apps/api/core';
import ImageSelectionPage from './ImageSelection';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtensio';
import { removeFromAlbum, viewYourAlbum } from 'api/api-functions/albums';

interface ImageManagementDialogProps {
  albumName: string | null;
  onClose: () => void;
  onSuccess: () => void;
  onError: (title: string, error: unknown) => void;
}

const ImageManagementDialog: React.FC<ImageManagementDialogProps> = ({
  albumName,
  onClose,
  onSuccess,
  onError,
}) => {
  const {
    successData: viewedAlbum,
    isLoading: isViewingAlbum,
    errorMessage: viewError,
  } = usePictoQuery({
    queryFn: async () => await viewYourAlbum(albumName || ''),
    queryKey: ['view-album', albumName],
  });

  const { mutate: removeImage, isPending: isRemovingImage } = usePictoMutation({
    mutationFn: removeFromAlbum,
    autoInvalidateTags: ['view-album', albumName || ''],
  });

  const [showImageSelection, setShowImageSelection] = useState(false);

  const handleRemoveImage = async (imageUrl: string) => {
    if (albumName) {
      try {
        await removeImage({ album_name: albumName, path: imageUrl });
        onSuccess();
      } catch (err) {
        onError('Error Removing Image', err);
      }
    }
  };

  const getImageName = (path: string) => {
    return path.split('\\').pop() || path.split('/').pop() || path;
  };

  if (viewError && viewError !== 'Something went wrong') {
    return <div>Error loading album: {viewError}</div>;
  }

  if (isViewingAlbum) {
    return <div>Loading...</div>;
  }

  if (showImageSelection) {
    return (
      <ImageSelectionPage
        albumName={albumName || ''}
        onClose={() => setShowImageSelection(false)}
        onSuccess={() => {
          setShowImageSelection(false);
          onSuccess();
        }}
        onError={onError}
      />
    );
  }

  return (
    <Dialog open={!!albumName} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Manage Images: {albumName}</DialogTitle>
        </DialogHeader>
        <div className="my-4">
          <Button onClick={() => setShowImageSelection(true)}>
            Add Images to Album
          </Button>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {viewedAlbum?.image_paths?.map((image: string, index: number) => {
            const srcc = convertFileSrc(image);
            return (
              <div key={index} className="relative">
                <img
                  src={srcc}
                  alt={`Album image ${getImageName(image)}`}
                  className="h-32 w-full rounded-lg object-cover"
                />
                <Button
                  onClick={() => handleRemoveImage(image)}
                  disabled={isRemovingImage}
                  className="absolute right-0 top-0 rounded-full bg-red-500 p-1 text-white"
                >
                  X
                </Button>
                <div className="absolute bottom-0 left-0 right-0 truncate rounded-b-lg bg-black bg-opacity-50 p-1 text-xs text-white">
                  {getImageName(image)}
                </div>
              </div>
            );
          })}
        </div>
        <DialogFooter>
          <Button onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ImageManagementDialog;
