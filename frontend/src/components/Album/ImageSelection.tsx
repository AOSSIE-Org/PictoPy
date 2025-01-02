import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { convertFileSrc } from '@tauri-apps/api/core';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtensio';
import { fetchAllImages } from '../../../api/api-functions/images';
import { addMultipleToAlbum } from '../../../api/api-functions/albums';
import { extractThumbnailPath } from '@/hooks/useImages';
import { useQueryClient } from '@tanstack/react-query';
interface ImageSelectionPageProps {
  albumName: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (title: string, error: unknown) => void;
}

const ImageSelectionPage: React.FC<ImageSelectionPageProps> = ({
  albumName,
  onClose,
  onSuccess,
  onError,
}) => {
  const queryClient = useQueryClient();
  const {
    successData: allImagesData,
    isLoading,
    errorMessage,
  } = usePictoQuery({
    queryFn: fetchAllImages,
    queryKey: ['all-images'],
  });

  const [selectedImages, setSelectedImages] = useState<string[]>([]);

  const { mutate: addMultipleImages, isPending: isAddingImages } =
    usePictoMutation({
      mutationFn: addMultipleToAlbum,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['view-album', albumName] });
        queryClient.invalidateQueries({ queryKey: ['all-albums'] });
      },
    });

  // Extract the array of image paths
  const allImages: string[] = allImagesData?.image_files || [];
  const imagesWithThumbnails = allImages.map((imagePath) => ({
    imagePath,
    url: convertFileSrc(imagePath),
    thumbnailUrl: convertFileSrc(
      extractThumbnailPath(allImagesData.folder_path, imagePath),
    ),
  }));
  useEffect(() => {
    if (errorMessage && errorMessage !== 'Something went wrong') {
      onError('Error Fetching Images', errorMessage);
    }
  }, [errorMessage, onError]);

  const toggleImageSelection = (imagePath: string) => {
    setSelectedImages((prev) =>
      prev.includes(imagePath)
        ? prev.filter((path) => path !== imagePath)
        : [...prev, imagePath],
    );
  };

  const handleAddSelectedImages = async () => {
    if (selectedImages.length > 0) {
      try {
        await addMultipleImages({
          album_name: albumName,
          paths: selectedImages,
        });
        onSuccess();
        setSelectedImages([]);
      } catch (err) {
        onError('Error Adding Images', err);
      }
    }
  };

  const getImageName = (path: string) => {
    return path.split('\\').pop() || path;
  };

  if (isLoading) {
    return <div>Loading images...</div>;
  }

  if (!Array.isArray(allImages) || allImages.length === 0) {
    return <div>No images available. Please add some images first.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="mb-4 text-2xl font-bold">Select Images for {albumName}</h1>
      {/* <FolderPicker setFolderPath={handleFolderPick} /> */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {imagesWithThumbnails.map(({ imagePath, thumbnailUrl }, index) => {
          return (
            <div key={index} className="relative">
              <div
                className={`rounded-full absolute -right-2 -top-2 z-10 h-6 w-6 cursor-pointer border-2 border-white ${
                  selectedImages.includes(imagePath)
                    ? 'bg-blue-500'
                    : 'bg-gray-300'
                }`}
                onClick={() => toggleImageSelection(imagePath)}
              />
              <img
                src={thumbnailUrl}
                alt={`Image ${getImageName(imagePath)}`}
                className="h-40 w-full rounded-lg object-cover"
              />
              <div className="absolute bottom-0 left-0 right-0 truncate rounded-b-lg bg-black bg-opacity-50 p-1 text-xs text-white">
                {getImageName(imagePath)}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex justify-between">
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleAddSelectedImages}
          disabled={isAddingImages || selectedImages.length === 0}
        >
          Add Selected Images ({selectedImages.length})
        </Button>
      </div>
    </div>
  );
};

export default ImageSelectionPage;
