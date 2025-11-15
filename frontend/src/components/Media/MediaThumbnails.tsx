import React, { useRef, useEffect } from 'react';
import { convertFileSrc } from '@tauri-apps/api/core';

interface MediaThumbnailsProps {
  images: Array<{
    id: string;
    path: string;
    thumbnailPath: string;
  }>;
  currentIndex: number;
  showThumbnails: boolean;
  onThumbnailClick: (index: number) => void;
  type?: string;
}

export const MediaThumbnails: React.FC<MediaThumbnailsProps> = ({
  images,
  currentIndex,
  showThumbnails,
  onThumbnailClick,
  type = 'image',
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const thumbnailRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const touchStartRef = useRef(0);
  const initialScrollLeftRef = useRef(0);

  useEffect(() => {
    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();

      const isTrackpad = Math.abs(e.deltaX) > Math.abs(e.deltaY);

      if (isTrackpad) {
        scrollContainer.scrollLeft += e.deltaX;
      } else {
        scrollContainer.scrollLeft += e.deltaY;
      }
    };

    const handleTouchStart = (e: TouchEvent) => {
      touchStartRef.current = e.touches[0].clientX;
      initialScrollLeftRef.current = scrollContainer.scrollLeft;
    };

    const handleTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      const currentX = e.touches[0].clientX;
      const deltaX = currentX - touchStartRef.current;
      const newScrollLeft = initialScrollLeftRef.current - deltaX;
      scrollContainer.scrollLeft = newScrollLeft;
    };

    scrollContainer.addEventListener('wheel', handleWheel, { passive: false });
    scrollContainer.addEventListener('touchstart', handleTouchStart, {
      passive: false,
    });
    scrollContainer.addEventListener('touchmove', handleTouchMove, {
      passive: false,
    });

    return () => {
      scrollContainer.removeEventListener('wheel', handleWheel);
      scrollContainer.removeEventListener('touchstart', handleTouchStart);
      scrollContainer.removeEventListener('touchmove', handleTouchMove);
    };
  }, []);

  useEffect(() => {
    if (showThumbnails) {
      const thumbnail = thumbnailRefs.current.get(currentIndex);
      const scrollContainer = scrollContainerRef.current;
      if (thumbnail && scrollContainer) {
        const containerWidth = scrollContainer.clientWidth;
        const thumbnailLeft = thumbnail.offsetLeft;
        const thumbnailWidth = thumbnail.clientWidth;

        const newScrollLeft =
          thumbnailLeft - containerWidth / 2 + thumbnailWidth / 2;

        scrollContainer.scrollTo({
          left: newScrollLeft,
          behavior: 'smooth',
        });
      }
    }
  }, [currentIndex, showThumbnails, images]);

  if (type !== 'image') return null;

  return (
    <div className="absolute bottom-0 w-full">
      <div
        ref={scrollContainerRef}
        className={`flex w-full items-center gap-2 overflow-x-auto bg-black/70 py-3 backdrop-blur-md transition-all duration-300 ${
          showThumbnails ? 'opacity-100' : 'opacity-0'
        } px-[calc(50%-3.5rem)]`}
      >
        {images.map((image, index) => (
          <div
            key={image.id}
            ref={(el) => {
              if (el) {
                thumbnailRefs.current.set(index, el);
              } else {
                thumbnailRefs.current.delete(index);
              }
            }}
            onClick={() => onThumbnailClick(index)}
            className={`relative h-20 w-28 flex-shrink-0 overflow-hidden rounded-lg ${
              index === currentIndex
                ? 'ring-2 ring-blue-500 ring-offset-1 ring-offset-black'
                : 'opacity-70 hover:opacity-100'
            } cursor-pointer transition-all duration-200 hover:scale-105`}
          >
            <img
              src={convertFileSrc(image.thumbnailPath) || '/placeholder.svg'}
              alt={`thumbnail-${index}`}
              className="h-full w-full object-cover"
              onError={(e) => {
                const img = e.target as HTMLImageElement;
                img.onerror = null;
                img.src = '/placeholder.svg';
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};
