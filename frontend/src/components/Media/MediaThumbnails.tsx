import React from 'react';
import { Heart } from 'lucide-react';
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
  favorites: string[];
  type?: string;
}

export const MediaThumbnails: React.FC<MediaThumbnailsProps> = ({
  images,
  currentIndex,
  showThumbnails,
  onThumbnailClick,
  favorites,
  type = 'image',
}) => {
  const isFavorite = (imagePath: string) => favorites.includes(imagePath);

  if (type !== 'image') return null;

  return (
    <div className="absolute bottom-0 w-full">
      <div
        className={`flex w-full items-center justify-center gap-2 overflow-x-auto bg-black/70 px-4 py-3 backdrop-blur-md transition-all duration-300 ${
          showThumbnails ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {images.map((image, index) => (
          <div
            key={image.id}
            onClick={() => onThumbnailClick(index)}
            className={`relative h-20 w-28 flex-shrink-0 overflow-hidden rounded-lg ${
              index === currentIndex
                ? 'ring-2 ring-blue-500 ring-offset-1 ring-offset-black'
                : 'opacity-70 hover:opacity-100'
            } cursor-pointer transition-all duration-200 hover:scale-105`}
          >
            {isFavorite(image.path) && (
              <div className="absolute top-1 right-1 z-10 rounded-full bg-black/30 p-0.5">
                <Heart className="h-3 w-3 fill-current text-rose-500" />
              </div>
            )}
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
