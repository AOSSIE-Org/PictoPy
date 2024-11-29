import React, { useState, useEffect } from 'react';
import {
  useViewAlbum,
  useRemoveImageFromAlbum,
} from '../../hooks/AlbumService';
import { Button } from '@/components/ui/button';
import { convertFileSrc } from '@tauri-apps/api/core';
import ImageSelectionPage from './ImageSelection';
import { AlbumData, AlbumViewProps } from '@/types/Album';
import MediaView from '../Media/MediaView';

const AlbumView: React.FC<AlbumViewProps> = ({
  albumName,
  onBack,
  onError,
}) => {
  const { album, viewAlbum, isLoading, error } = useViewAlbum();
  const { removeImage, isLoading: isRemovingImage } = useRemoveImageFromAlbum();
  const [showImageSelection, setShowImageSelection] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(
    null,
  );

  useEffect(() => {
    viewAlbum(albumName).catch((err) => onError('Error loading album', err));
  }, [albumName, viewAlbum, onError]);

  const handleRemoveImage = async (imageUrl: string) => {
    try {
      await removeImage(albumName, imageUrl);
      await viewAlbum(albumName);
    } catch (err) {
      onError('Error Removing Image', err);
    }
  };

  const handleImageClick = (index: number) => {
    setSelectedImageIndex(index);
  };

  const handleCloseMediaView = () => {
    setSelectedImageIndex(null);
  };

  if (isLoading) return <div>Loading album...</div>;
  if (error) return <div>Error loading album: {error.message}</div>;
  if (!album) return <div>No album data available.</div>;

  if (showImageSelection) {
    return (
      <ImageSelectionPage
        albumName={albumName}
        onClose={() => setShowImageSelection(false)}
        onSuccess={() => {
          setShowImageSelection(false);
          viewAlbum(albumName);
        }}
        onError={onError}
      />
    );
  }

  const albumData = album as unknown as AlbumData;

  // Convert all image paths to their correct source URLs
  const convertedImagePaths = albumData.photos.map((path) =>
    convertFileSrc(path),
  );

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <Button onClick={onBack} variant="outline">
          Back to Albums
        </Button>
        <Button onClick={() => setShowImageSelection(true)} variant="outline">
          Add Images
        </Button>
      </div>

      {albumData.photos && albumData.photos.length > 0 ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {convertedImagePaths.map((srcc, index) => (
            <div key={index} className="relative">
              <img
                src={srcc}
                alt={`Album image ${index + 1}`}
                className="h-40 w-full cursor-pointer rounded-lg object-cover"
                onClick={() => handleImageClick(index)}
              />
              <Button
                onClick={() => handleRemoveImage(albumData.photos[index])}
                disabled={isRemovingImage}
                className="absolute right-2 top-2 rounded-full bg-red-500 p-1 text-white"
              >
                X
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <div>This album is empty. Add some images to get started!</div>
      )}

      {selectedImageIndex !== null && (
        <MediaView
          initialIndex={selectedImageIndex}
          onClose={handleCloseMediaView}
          allMedia={convertedImagePaths}
          currentPage={1}
          itemsPerPage={albumData.photos.length}
          type="image"
        />
      )}
    </div>
  );
};

export default AlbumView;
