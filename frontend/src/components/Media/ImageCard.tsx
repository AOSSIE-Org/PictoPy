import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Check, Heart, Share2 } from 'lucide-react';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Image } from '@/types/Media';
import { ImageTags } from './ImageTags';
import { setCurrentViewIndex } from '@/features/imageSlice';
import { toggleImageSelection } from '@/features/albumSlice';
import { selectIsSelectionMode, selectIsImageSelected } from '@/features/albumSelectors';
import { convertFileSrc } from '@tauri-apps/api/core';

interface ImageCardProps {
  image: Image;
  imageIndex: number;
  className?: string;
  isSelected?: boolean;
  showTags?: boolean;
}

export function ImageCard({
  image,
  imageIndex,
  className,
  isSelected = false,
  showTags = true,
}: ImageCardProps) {
  const dispatch = useDispatch();
  const [isFavorite, setIsFavorite] = React.useState(false);
  const [isImageHovered, setIsImageHovered] = React.useState(false);

  // Selection mode state from Redux
  const isSelectionMode = useSelector(selectIsSelectionMode);
  const isImageSelected = useSelector(selectIsImageSelected(image.id));

  // Default to empty array if no tags are provided
  const tags = image.tags || [];

  const handleImageClick = React.useCallback(() => {
    if (isSelectionMode) {
      // In selection mode, toggle selection
      dispatch(toggleImageSelection(image.id));
    } else {
      // Normal mode, open image view
      dispatch(setCurrentViewIndex(imageIndex));
    }
  }, [dispatch, imageIndex, isSelectionMode, image.id]);

  // Use selection state from Redux when in selection mode, otherwise use prop
  const actuallySelected = isSelectionMode ? isImageSelected : isSelected;

  return (
    <div
      className={cn(
        'group bg-card cursor-pointer overflow-hidden rounded-lg border transition-all hover:shadow-md',
        actuallySelected ? 'ring-2 ring-[#4088fa]' : '',
        className,
      )}
      onMouseEnter={() => setIsImageHovered(true)}
      onMouseLeave={() => setIsImageHovered(false)}
      onClick={handleImageClick}
    >
      <div className="relative">
        {/* Selection tick mark */}
        {actuallySelected && (
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
              actuallySelected ? 'opacity-95' : '',
            )}
          />
          {/* Dark overlay on hover */}
          <div className="absolute inset-0 bg-black/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />

          {/* Image actions on hover */}
          <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full bg-white/20 text-white hover:!bg-white/40 hover:!text-white"
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation();
                setIsFavorite(!isFavorite);
              }}
            >
              <Heart
                className={cn(
                  'h-5 w-5',
                  isFavorite ? 'fill-brand-orange text-brand-orange' : '',
                )}
              />
              <span className="sr-only">Favorite</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full bg-white/20 text-white hover:!bg-white/40 hover:!text-white"
              onClick={(e: React.MouseEvent) => e.stopPropagation()}
            >
              <Share2 className="h-5 w-5" />
              <span className="sr-only">Share</span>
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
