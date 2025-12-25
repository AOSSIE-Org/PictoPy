import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Check, Heart, MoreVertical, Plus, Trash } from 'lucide-react';
import { useCallback, useState } from 'react';
import { Image } from '@/types/Media';
import { ImageTags } from './ImageTags';
import { convertFileSrc } from '@tauri-apps/api/core';
import { useToggleFav } from '@/hooks/useToggleFav';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { AddToAlbumDialog } from '@/components/Dialog/AddToAlbumDialog';

interface ImageCardViewProps {
  image: Image;
  className?: string;
  isSelected?: boolean;
  showTags?: boolean;
  onClick?: () => void;
  imageIndex?: number;
  albumId?: string;
  onRemoveFromAlbum?: (imageId: string) => void;
}

export function ImageCard({
  image,
  className,
  isSelected = false,
  showTags = true,
  onClick,
  albumId,
  onRemoveFromAlbum,
}: ImageCardViewProps) {
  const [isImageHovered, setIsImageHovered] = useState(false);
  const [isAddToAlbumOpen, setIsAddToAlbumOpen] = useState(false);
  // Default to empty array if no tags are provided
  const tags = image.tags || [];
  const { toggleFavourite } = useToggleFav();

  const handleToggleFavourite = useCallback(() => {
    if (image?.id) {
      toggleFavourite(image.id);
    }
  }, [image, toggleFavourite]);

  return (
    <>
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
            <div className="absolute inset-x-0 top-2 flex items-center justify-between px-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
              {/* Left side actions */}
              <div></div>

              {/* Right side actions */}
              <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                <Button
                  variant="ghost"
                  size="icon"
                  className={`h-8 w-8 rounded-full text-white transition-all duration-300 ${
                    image.isFavourite
                      ? 'bg-rose-500/80 hover:bg-rose-600'
                      : 'bg-black/40 hover:bg-black/60'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleFavourite();
                  }}
                >
                  {image.isFavourite ? (
                    <Heart className="h-4 w-4" fill="currentColor"></Heart>
                  ) : (
                    <Heart className="h-4 w-4" />
                  )}
                </Button>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 rounded-full bg-black/40 text-white transition-all duration-300 hover:bg-black/60"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {albumId && onRemoveFromAlbum ? (
                      <DropdownMenuItem
                        onClick={() => onRemoveFromAlbum(image.id)}
                        className="text-red-500 focus:bg-red-50 focus:text-red-500"
                      >
                        <Trash className="mr-2 h-4 w-4" />
                        Remove from Album
                      </DropdownMenuItem>
                    ) : (
                      <DropdownMenuItem
                        onClick={() => setIsAddToAlbumOpen(true)}
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        Add to Album
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
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

      <AddToAlbumDialog
        isOpen={isAddToAlbumOpen}
        onClose={() => setIsAddToAlbumOpen(false)}
        imageIds={[image.id]}
      />
    </>
  );
}
