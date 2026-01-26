import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Check, Heart, Trash2 } from 'lucide-react';
import { useCallback, useState } from 'react';
import { Image } from '@/types/Media';
import { ImageTags } from './ImageTags';
import { convertFileSrc } from '@tauri-apps/api/core';
import { useToggleFav } from '@/hooks/useToggleFav';
import { useDispatch, useSelector } from 'react-redux';
import { toggleImageSelection } from '@/features/imageSlice';
import { selectIsSelectionMode, selectSelectedImages } from '@/features/imageSelectors';
import { useDeleteImage } from '@/hooks/useDeleteImage';

interface ImageCardViewProps {
  image: Image;
  className?: string;
  showTags?: boolean;
  onClick?: () => void;
  imageIndex?: number;
}

export function ImageCard({
  image,
  className,
  showTags = true,
  onClick,
}: ImageCardViewProps) {
  const [isImageHovered, setIsImageHovered] = useState(false);
  // Default to empty array if no tags are provided
  const tags = image.tags || [];
  const { toggleFavourite } = useToggleFav();
  const dispatch = useDispatch();
  const isSelectionMode = useSelector(selectIsSelectionMode);
  const selectedImages = useSelector(selectSelectedImages);
  const isImageSelected = selectedImages.includes(image.id);
  const { deleteSingleImage } = useDeleteImage();


  const handleToggleFavourite = useCallback(() => {
    if (image?.id) {
      toggleFavourite(image.id);
    }
  }, [image, toggleFavourite]);

  const handleImageClick = useCallback(() => {
    if (isSelectionMode) {
      dispatch(toggleImageSelection(image.id));
    } else if (onClick) {
      onClick();
    }
  }, [isSelectionMode, dispatch, image.id, onClick]);
  return (
    <div
      className={cn(
        'group bg-card cursor-pointer overflow-hidden rounded-lg border transition-all hover:shadow-md',
        isImageSelected ? 'ring-2 ring-[#4088fa]' : '',
        className,
      )}
      onMouseEnter={() => setIsImageHovered(true)}
      onMouseLeave={() => setIsImageHovered(false)}
      onClick={handleImageClick}
    >
      <div className="relative">
        {/* Selection tick mark */}
        {isImageSelected && (
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
              isImageSelected ? 'opacity-95' : '',
            )}
          />
          {/* Dark overlay on hover */}
          <div className="absolute inset-0 bg-black/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />

          {/* Image actions on hover */}
          {!isSelectionMode && (
            <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
              <Button
                variant="ghost"
                size="icon"
                className={`cursor-pointer rounded-full p-2.5 text-white transition-all duration-300 ${
                  image.isFavourite
                    ? 'bg-rose-500/80 hover:bg-rose-600 hover:shadow-lg'
                    : 'bg-white/10 hover:bg-white/20 hover:shadow-lg'
                }`}
                onClick={(e) => {
                  console.log(image);
                  e.stopPropagation();
                  handleToggleFavourite();
                }}
              >
                {image.isFavourite ? (
                  <Heart className="h-5 w-5" fill="currentColor"></Heart>
                ) : (
                  <Heart className="h-5 w-5" />
                )}
                <span className="sr-only">Favourite</span>
              </Button>

              <Button
    variant="ghost"
    size="icon"
    className="rounded-full bg-red-500/80 p-2.5 text-white hover:bg-red-600"
    onClick={(e) => {
      e.stopPropagation();
      deleteSingleImage(image.id);
    }}
  >
    <Trash2 className="h-5 w-5" />
  </Button>
            </div>
          )}
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
