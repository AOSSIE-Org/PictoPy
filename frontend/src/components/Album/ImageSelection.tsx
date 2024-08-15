import React, { useState, useEffect } from "react";
import { useFetchAllImages } from "@/hooks/UseVideos";
import { useAddMultipleImagesToAlbum } from "../../hooks/AlbumService";
import { Button } from "@/components/ui/button";
import { convertFileSrc } from "@tauri-apps/api/core";
import FolderPicker from "../FolderPicker/FolderPicker";
import { useAddFolder } from "@/hooks/AI_Image";

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
  const { images: allImagesData, isLoading, error } = useFetchAllImages();
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const { addMultipleImages, isLoading: isAddingImages } =
    useAddMultipleImagesToAlbum();

  // Extract the array of image paths
  const allImages: string[] = allImagesData?.images || [];

  useEffect(() => {
    if (error) {
      onError("Error Fetching Images", error);
    }
  }, [error, onError]);

  const toggleImageSelection = (imagePath: string) => {
    setSelectedImages((prev) =>
      prev.includes(imagePath)
        ? prev.filter((path) => path !== imagePath)
        : [...prev, imagePath]
    );
  };

  const handleAddSelectedImages = async () => {
    if (selectedImages.length > 0) {
      try {
        await addMultipleImages(albumName, selectedImages);
        onSuccess();
        setSelectedImages([]);
      } catch (err) {
        onError("Error Adding Images", err);
      }
    }
  };

  const getImageName = (path: string) => {
    return path.split("\\").pop() || path;
  };

  if (isLoading) {
    return <div>Loading images...</div>;
  }

  if (!Array.isArray(allImages) || allImages.length === 0) {
    return <div>No images available. Please add some images first.</div>;
  }
  const handleFolderPick = async (path: string) => {
    try {
      await useAddFolder(path);
    } catch (error) {
      console.error("Error adding folder:", error);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Select Images for {albumName}</h1>
      {/* <FolderPicker setFolderPath={handleFolderPick} /> */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {allImages.map((imagePath, index) => {
          const srcc = convertFileSrc(imagePath);
          return (
            <div key={index} className="relative">
              <div
                className={`absolute -top-2 -right-2 w-6 h-6 rounded-full border-2 border-white cursor-pointer z-10 ${
                  selectedImages.includes(imagePath)
                    ? "bg-blue-500"
                    : "bg-gray-300"
                }`}
                onClick={() => toggleImageSelection(imagePath)}
              />
              <img
                src={srcc}
                alt={`Image ${getImageName(imagePath)}`}
                className="w-full h-40 object-cover rounded-lg"
              />
              <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 truncate rounded-b-lg">
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
