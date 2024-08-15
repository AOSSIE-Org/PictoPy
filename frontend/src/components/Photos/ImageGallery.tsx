// File: components/Images/ImageGallery.tsx

import { useState, useMemo } from "react";

import { sortImages } from "@/utils/imageUtils";
import SortingControls from "./PhotoGallery/SortingControls";
import ImageGrid from "./PhotoGallery/ImageGrid";
import ImageView from "./PhotoGallery/PhotosView";
import PaginationControls from "../Videos/VideoGallery/Pagination";

import { ImageGalleryProps } from "@/types/image";

export default function ImageGallery({ images, title }: ImageGalleryProps) {
  const [sortBy, setSortBy] = useState<"date" | "title" | "popularity">("date");
  const [imagesPerRow, setImagesPerRow] = useState<number>(3);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showImageViewer, setShowImageViewer] = useState<boolean>(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0);
  const imagesPerPage: number = 9;

  const sortedImages = useMemo(
    () => sortImages(images, sortBy),
    [sortBy, images]
  );

  const indexOfLastImage = currentPage * imagesPerPage;
  const indexOfFirstImage = indexOfLastImage - imagesPerPage;
  const currentImages = sortedImages.slice(indexOfFirstImage, indexOfLastImage);
  const totalPages = Math.ceil(sortedImages.length / imagesPerPage);

  const openImageViewer = (index: number) => {
    setSelectedImageIndex(index);
    setShowImageViewer(true);
  };

  const closeImageViewer = () => {
    setShowImageViewer(false);
  };

  return (
    <div className="dark:bg-background dark:text-foreground max-w-6xl mx-auto px-4 md:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{title}</h1>
        <SortingControls
          sortBy={sortBy}
          setSortBy={setSortBy}
          imagesPerRow={imagesPerRow}
          setImagesPerRow={setImagesPerRow}
        />
      </div>
      <ImageGrid
        images={currentImages}
        imagesPerRow={imagesPerRow}
        openImageViewer={openImageViewer}
      />
      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
      {showImageViewer && (
        <ImageView
          images={images.map((img) => img.src)}
          initialIndex={selectedImageIndex}
          onClose={closeImageViewer}
        />
      )}
    </div>
  );
}
