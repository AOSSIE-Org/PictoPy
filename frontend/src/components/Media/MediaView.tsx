// components/MediaGallery/MediaView.tsx
import { MediaViewProps } from '@/types/Media';
import React, { useEffect, useState } from 'react';

const MediaView: React.FC<MediaViewProps> = ({
  initialIndex,
  onClose,
  allMedia,
  currentPage,
  itemsPerPage,
  type,
}) => {
  const [globalIndex, setGlobalIndex] = useState<number>(
    (currentPage - 1) * itemsPerPage + initialIndex,
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
    <div className="fixed left-0 top-0 z-50 flex h-full w-full items-center justify-center bg-black bg-opacity-90">
      <button
        onClick={onClose}
        className="absolute left-4 top-4 z-0 rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
      >
        Back
      </button>
      {type === 'image' ? (
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
        className="duration-20 absolute left-4 top-1/2 -translate-y-1/2 transform rounded-md border border-black bg-white p-2 text-sm text-black transition hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
      >
        {'<'}
      </button>
      <button
        onClick={handleNextItem}
        className="absolute right-4 top-1/2 -translate-y-1/2 transform rounded-md border border-black bg-white p-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
      >
        {'>'}
      </button>
    </div>
  );
};

export default MediaView;
