import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Check, Heart, Share2, Copy, FileArchive, FolderOpen } from 'lucide-react';
import { useCallback, useState } from 'react';
import { Image } from '@/types/Media';
import { ImageTags } from './ImageTags';
import { convertFileSrc } from '@tauri-apps/api/core';
import { useToggleFav } from '@/hooks/useToggleFav';
import { useImageShare } from '@/hooks/useImageShare';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

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
  const [isImageHovered, setIsImageHovered] = useState(false);
  // Default to empty array if no tags are provided
  const tags = image.tags || [];
  const { toggleFavourite } = useToggleFav();
  const { exportAsZip, copyPathToClipboard, openFileLocation, isSharing } = useImageShare();

  const handleToggleFavourite = useCallback(() => {
    if (image?.id) {
      toggleFavourite(image.id);
    }
  }, [image, toggleFavourite]);

  const handleExportAsZip = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    await exportAsZip(image);
  }, [image, exportAsZip]);

  const handleCopyPath = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    await copyPathToClipboard(image);
  }, [image, copyPathToClipboard]);

  const handleOpenLocation = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    await openFileLocation(image);
  }, [image, openFileLocation]);
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

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="cursor-pointer rounded-full bg-white/20 text-white hover:!bg-white/40 hover:!text-white focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 data-[state=open]:bg-white/40"
                  onClick={(e) => e.stopPropagation()}
                  title="Share"
                  aria-label="Share"
                  disabled={isSharing}
                >
                  <Share2 className="h-5 w-5" />
                  <span className="sr-only">Share</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleExportAsZip} className="cursor-pointer">
                  <FileArchive className="mr-2 h-4 w-4" />
                  Export as ZIP
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleOpenLocation} className="cursor-pointer">
                  <FolderOpen className="mr-2 h-4 w-4" />
                  Open File Location
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleCopyPath} className="cursor-pointer">
                  <Copy className="mr-2 h-4 w-4" />
                  Copy Path
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
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
