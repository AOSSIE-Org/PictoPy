import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Check, Heart } from 'lucide-react';
import { useState } from 'react';
import { Image } from '@/types/Media';
import { ImageTags } from './ImageTags';
import { convertFileSrc } from '@tauri-apps/api/core';

interface ImageCardViewProps {
  image: Image;
  className?: string;
  isSelected?: boolean;
  showTags?: boolean;
  onClick?: () => void;
  imageIndex?: number;
}

export function ImageCard({
  image,
  className,
  isSelected = false,
  showTags = true,
  onClick,
}: ImageCardViewProps) {
  const [isFavorite, setIsFavorite] = useState(false);
  const [isImageHovered, setIsImageHovered] = useState(false);

  // Default to empty array if no tags are provided
  const tags = image.tags || [];

  return (
    <div
      className={cn(
        'group bg-card cursor-pointer overflow-hidden rounded-lg border transition-all hover:shadow-md',
        isSelected ? 'ring-2 ring-[#4088fa]' : '',
        className,
      )}
      onMouseEnter={() => setIsImageHovered(true)}
      onMouseLeave={() => setIsImageHovered(false)}
      onClick={onClick}
    >
      <div className="relative">
        {/* Selection tick mark */}
        {isSelected && (
          <div className="absolute top-2 right-2 z-10 rounded-full bg-[#4088fa] p-1">
            <Check className="h-4 w-4 text-white" />
          </div>
        )}

        <AspectRatio ratio={1}>
          <img
            src={convertFileSrc(
              image.thumbnailPath || image.path || '/placeholder.svg',
            )}
            alt={'Sample Title'}
            className={cn(
              'h-full w-full object-cover transition-transform group-hover:scale-105',
              isSelected ? 'opacity-95' : '',
            )}
          />
          {/* Dark overlay on hover */}
          <div className="absolute inset-0 bg-black/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />

          {/* Image actions on hover */}
          <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
            <Button
              variant="ghost"
              size="icon"
              className="cursor-pointer rounded-full bg-white/20 text-white hover:!bg-white/40 hover:!text-white"
              onClick={(e) => {
                e.stopPropagation();
                setIsFavorite(!isFavorite);
              }}
              title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
              aria-label="Add to Favorites"
            >
              <Heart
                className={cn(
                  'h-5 w-5',
                  isFavorite ? 'fill-brand-orange text-brand-orange' : '',
                )}
              />
              <span className="sr-only">Favorite</span>
            </Button>
          </div>
        </AspectRatio>

        {/* Tag section */}
        <ImageTags
          tags={tags}
          showTags={showTags}
          isImageHovered={isImageHovered}
        />
      </div>
    </div>
  );
}
