import type { CSSProperties, PropsWithChildren } from 'react';
import { cn } from '@/lib/utils';
import { GALLERY_GRID_SIZES, useGalleryView } from '@/hooks/useGalleryView';

interface GalleryGridProps extends PropsWithChildren {
  className?: string;
}

export function GalleryGrid({ children, className }: GalleryGridProps) {
  const [size] = useGalleryView();
  const { minWidth, gap } = GALLERY_GRID_SIZES[size];
  const style: CSSProperties = {
    gridTemplateColumns: `repeat(auto-fill, minmax(min(100%, ${minWidth}px), 1fr))`,
    gap: `${gap}px`,
  };

  return (
    <div
      className={cn('grid', className)}
      data-gallery-size={size}
      style={style}
    >
      {children}
    </div>
  );
}
