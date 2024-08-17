import React, { useState, useEffect } from "react";
import {
  useViewAlbum,
  useRemoveImageFromAlbum,
} from "../../hooks/AlbumService";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { convertFileSrc } from "@tauri-apps/api/core";
import ImageSelectionPage from "./ImageSelection";

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
    album: viewedAlbum,
    viewAlbum,
    isLoading: isViewingAlbum,
    error: viewError,
  } = useViewAlbum();
  const { removeImage, isLoading: isRemovingImage } = useRemoveImageFromAlbum();
  const [showImageSelection, setShowImageSelection] = useState(false);

  useEffect(() => {
    if (albumName) {
      viewAlbum(albumName).catch((err) => onError("Error loading album", err));
    }
  }, [albumName, viewAlbum, onError]);

  const handleRemoveImage = async (imageUrl: string) => {
    if (albumName) {
      try {
        await removeImage(albumName, imageUrl);
        await viewAlbum(albumName);
        onSuccess();
      } catch (err) {
        onError("Error Removing Image", err);
      }
    }
  };

  const getImageName = (path: string) => {
    return path.split("\\").pop() || path;
  };

  if (viewError) {
    return <div>Error loading album: {viewError.message}</div>;
  }

  if (isViewingAlbum) {
    return <div>Loading...</div>;
  }

  if (showImageSelection) {
    return (
      <ImageSelectionPage
        albumName={albumName || ""}
        onClose={() => setShowImageSelection(false)}
        onSuccess={() => {
          setShowImageSelection(false);
          viewAlbum(albumName || "");
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
          {viewedAlbum?.image_paths?.map((image, index) => {
            const srcc = convertFileSrc(image);
            return (
              <div key={index} className="relative">
                <img
                  src={srcc}
                  alt={`Album image ${getImageName(image)}`}
                  className="w-full h-32 object-cover rounded-lg"
                />
                <Button
                  onClick={() => handleRemoveImage(image)}
                  disabled={isRemovingImage}
                  className="absolute top-0 right-0 bg-red-500 text-white p-1 rounded-full"
                >
                  X
                </Button>
                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 truncate rounded-b-lg">
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
