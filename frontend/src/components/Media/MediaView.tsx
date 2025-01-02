import { MediaViewProps } from '@/types/Media';
import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

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
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setGlobalIndex((currentPage - 1) * itemsPerPage + initialIndex);
  }, [initialIndex, currentPage, itemsPerPage]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowRight') {
        handleNextItem();
      } else if (e.key === 'ArrowLeft') {
        handlePrevItem();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [globalIndex, onClose]);

  const handelZoomOut = () => {
    setScale((s) => Math.max(0.1, s - 0.1));
  };
  const handelZoomIn = () => {
    setScale((s) => Math.min(4, s + 0.1));
  };

  const handleWheel = (e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY * -0.01;
    const newScale = Math.min(Math.max(0.1, scale + delta), 4);
    setScale(newScale);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetZoom = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  useEffect(() => {
    const element = document.getElementById('zoomable-image');
    element?.addEventListener('wheel', handleWheel, { passive: false });
    return () => element?.removeEventListener('wheel', handleWheel);
  }, [scale]);

  function handlePrevItem() {
    if (globalIndex > 0) {
      setGlobalIndex(globalIndex - 1);
    }
    resetZoom();
  }

  function handleNextItem() {
    if (globalIndex < allMedia.length - 1) {
      setGlobalIndex(globalIndex + 1);
    }
    resetZoom();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black bg-opacity-90" />

      <div
        className="relative z-50 flex h-full w-full items-center justify-center"
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            onClose();
          }
        }}
      >
        <button
          onClick={onClose}
          className="absolute left-4 top-4 z-50 rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
        >
          Back
        </button>

        {type === 'image' ? (
          <div
            id="zoomable-image"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className="relative flex h-full w-full items-center justify-center overflow-hidden align-middle"
          >
            <img
              src={allMedia[globalIndex]}
              alt={`image-${globalIndex}`}
              draggable={false}
              className="max-h-full select-none"
              style={{
                transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                transition: isDragging ? 'none' : 'transform 0.1s',
                cursor: isDragging ? 'grabbing' : 'grab',
              }}
            />
            <div className="absolute bottom-4 right-4 flex gap-2">
              <button
                onClick={handelZoomOut}
                className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
              >
                -
              </button>
              <button
                onClick={resetZoom}
                className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
              >
                Reset
              </button>
              <button
                onClick={handelZoomIn}
                className="rounded-md border border-black bg-white px-4 py-2 text-sm text-black transition duration-200 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)]"
              >
                +
              </button>
            </div>
          </div>
        ) : (
          <video
            src={allMedia[globalIndex]}
            className="max-h-full"
            controls
            autoPlay
          />
        )}

        {globalIndex > 0 && (
          <button
            onClick={handlePrevItem}
            className="absolute left-4 top-1/2 z-50 flex items-center rounded-[50%] border border-black bg-white p-2 text-black transition duration-100 hover:bg-slate-800 hover:text-white"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>
        )}
        {globalIndex < allMedia.length - 1 && (
          <button
            onClick={handleNextItem}
            className="absolute right-4 top-1/2 z-50 flex items-center rounded-[50%] border border-black bg-white p-2 text-black transition duration-100 hover:bg-slate-800 hover:text-white"
          >
            <ChevronRight className="h-6 w-6" />
          </button>
        )}
      </div>
    </div>
  );
};

export default MediaView;
