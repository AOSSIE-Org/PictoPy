// components/MediaGallery/MediaView.tsx
import { MediaViewProps } from "@/types/Media";
import React, { useEffect, useState } from "react";

const MediaView: React.FC<MediaViewProps> = ({
  initialIndex,
  onClose,
  allMedia,
  currentPage,
  itemsPerPage,
  type,
}) => {
  const [globalIndex, setGlobalIndex] = useState<number>(
    (currentPage - 1) * itemsPerPage + initialIndex
  );

  useEffect(() => {
    setGlobalIndex((currentPage - 1) * itemsPerPage + initialIndex);
  }, [initialIndex, currentPage, itemsPerPage]);

  function handlePrevItem() {
    if (globalIndex > 0) {
      setGlobalIndex(globalIndex - 1);
    } else {
      setGlobalIndex(allMedia.length - 1);
    }
  }

  function handleNextItem() {
    if (globalIndex < allMedia.length - 1) {
      setGlobalIndex(globalIndex + 1);
    } else {
      setGlobalIndex(0);
    }
  }

  return (
    <div className="fixed top-0 left-0 w-full h-full flex justify-center items-center bg-black bg-opacity-90 z-50">
      <button
        onClick={onClose}
        className="absolute z-0 top-4 left-4 px-4 py-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-200"
      >
        Back
      </button>
      {type === "image" ? (
        <img
          src={allMedia[globalIndex]}
          alt={`image-${globalIndex}`}
          className="max-h-full"
        />
      ) : (
        <video
          src={allMedia[globalIndex]}
          className="max-h-full"
          controls
          autoPlay
        />
      )}
      <button
        onClick={handlePrevItem}
        className="absolute top-1/2 left-4 transform -translate-y-1/2 p-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-20"
      >
        {"<"}
      </button>
      <button
        onClick={handleNextItem}
        className="absolute top-1/2 right-4 transform -translate-y-1/2 p-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-200"
      >
        {">"}
      </button>
    </div>
  );
};

export default MediaView;
