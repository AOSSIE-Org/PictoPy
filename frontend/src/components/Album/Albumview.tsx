import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { convertFileSrc } from '@tauri-apps/api/core';
import ImageSelectionPage from './ImageSelection';
import { AlbumData, AlbumViewProps } from '@/types/Album';
import MediaView from '../Media/MediaView';
import { CircleX, ArrowLeft, ImagePlus } from 'lucide-react';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtensio';
import {
  removeFromAlbum,
  viewYourAlbum,
} from '../../../api/api-functions/albums';
import { extractThumbnailPath } from '@/hooks/useImages';
import { useQueryClient } from '@tanstack/react-query';
const AlbumView: React.FC<AlbumViewProps> = ({
  albumName,
  onBack,
  onError,
}) => {
  const queryClient = useQueryClient();
  const {
    successData: album,
    isLoading,
    errorMessage: error,
  } = usePictoQuery({
    queryFn: async () => await viewYourAlbum(albumName),
    queryKey: ['view-album', albumName],
  });
  const { mutate: removeImage, isPending: isRemovingImage } = usePictoMutation({
    mutationFn: removeFromAlbum,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['view-album', albumName],
      });
      queryClient.invalidateQueries({ queryKey: ['all-albums'] });
    },
  });
  const [showImageSelection, setShowImageSelection] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(
    null,
  );

  const handleRemoveImage = async (imageUrl: string) => {
    try {
      await removeImage({ album_name: albumName, path: imageUrl });
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
  if (error && error !== 'Something went wrong')
    return <div>Error loading album: {error}</div>;
  if (!album) return <div>No album data available.</div>;

  if (showImageSelection) {
    return (
      <ImageSelectionPage
        albumName={albumName}
        onClose={() => setShowImageSelection(false)}
        onSuccess={() => {
          setShowImageSelection(false);
        }}
        onError={onError}
      />
    );
  }

  const albumData = album as unknown as AlbumData;

  // Convert all image paths to their correct source URLs
  const convertedImagePaths = albumData.photos.map((path) => {
    return {
      url: convertFileSrc(path),
      thumbnailUrl: convertFileSrc(
        extractThumbnailPath(albumData.folder_path, path),
      ),
    };
  });

  // console.log(convertedImagePaths);
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
          {convertedImagePaths.map(({ thumbnailUrl }, index) => (
            <div key={index} className="relative h-56">
              <img
                src={thumbnailUrl}
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
          allMedia={convertedImagePaths.map((image) => {
            return { url: image.url };
          })}
          currentPage={1}
          itemsPerPage={albumData.photos.length}
          type="image"
        />
      )}
    </div>
  );
};

export default AlbumView;
