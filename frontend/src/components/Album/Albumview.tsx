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
import { CircleX, ArrowLeft, ImagePlus } from 'lucide-react';
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
    <div className="mx-auto pb-4 pt-1">
      <div className="mb-4 flex items-center justify-between">
        <Button onClick={onBack} variant="outline">
          <ArrowLeft className="h-[18px] w-[18px]" />
          <p className="mb-[1px] ml-1"> Back to Albums</p>
        </Button>
        <Button onClick={() => setShowImageSelection(true)} variant="outline">
          <ImagePlus className="h-[18px] w-[18px]" />
          <p className="ml-2"> Add Images</p>
        </Button>
      </div>

      {albumData.photos && albumData.photos.length > 0 ? (
        <div className="grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4">
          {convertedImagePaths.map((srcc, index) => (
            <div key={index} className="relative h-56">
              <img
                src={srcc}
                alt={`Album image ${index + 1}`}
                className="h-full w-full cursor-pointer rounded-lg object-cover"
                onClick={() => handleImageClick(index)}
              />
              <button
                onClick={() => handleRemoveImage(albumData.photos[index])}
                disabled={isRemovingImage}
                className="rounded-[50%]transition-transform absolute right-2 top-2 h-6 w-6 duration-300"
              >
                <CircleX className="h-6 w-6 fill-red-500 stroke-1 text-white opacity-50 hover:opacity-100" />
              </button>
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
