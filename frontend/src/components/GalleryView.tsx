// src/components/GalleryView.tsx

import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { convertFileSrc } from '@tauri-apps/api/core';
import { RootState } from '@/app/store';
import { ChronologicalGallery, MonthMarker } from '@/components/Media/ChronologicalGallery';
import type { Image as MediaImage } from '@/types/Media';
import { setCurrentViewIndex } from '@/features/imageSlice';
import { selectIsImageViewOpen } from '@/features/imageSelectors';
import { MediaView } from '@/components/Media/MediaView';
import { Button } from '@/components/ui/button';
import { Heart, Share2 } from 'lucide-react';
import { useToggleFav } from '@/hooks/useToggleFav';

/**
 * This component is tolerant of different Image shapes:
 * - offline/tauri style: thumbnailPath, path, name, metadata
 * - online style: url, filename, date
 *
 * It will try to prefer thumbnailPath -> url -> path.
 */

type AnyImage = Partial<MediaImage> & {
  id: string | number;
  thumbnailPath?: string;
  path?: string;
  url?: string;
  filename?: string;
  name?: string;
  metadata?: Record<string, any>;
  date?: string;
};

interface Props {
  images: AnyImage[];
  title: string;
  scrollableRef: React.RefObject<HTMLDivElement | null>;
  onMonthOffsetsChange: (v: MonthMarker[] | any) => void;
}

const toTauriUrl = (p?: string) => {
  if (!p) return undefined;
  try {
    const fixed = p.replace(/\\/g, '/');
    return convertFileSrc(fixed);
  } catch {
    // convertFileSrc may throw if not running in Tauri; fallback to raw path
    return p;
  }
};

const getImageSrc = (img: AnyImage) => {
  // Order of preference:
  // 1. url (if exists)
  if (img.url && typeof img.url === 'string') return img.url;
  // 2. thumbnailPath (tauri local)
  if (img.thumbnailPath && typeof img.thumbnailPath === 'string') {
    const v = toTauriUrl(img.thumbnailPath);
    if (v) return v;
  }
  // 3. path (original file path)
  if (img.path && typeof img.path === 'string') {
    const v = toTauriUrl(img.path);
    if (v) return v;
  }
  // 4. fallback placeholder
  return '/placeholder.svg';
};

export const GalleryView: React.FC<Props> = ({
  images,
  title,
  scrollableRef,
  onMonthOffsetsChange,
}) => {
  const dispatch = useDispatch();
  const mode = useSelector((s: RootState) => s.viewMode.mode);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const { toggleFavourite } = useToggleFav();

  const handleImageClick = useCallback(
    (index: number) => {
      dispatch(setCurrentViewIndex(index));
    },
    [dispatch],
  );

  const handleToggleFavourite = useCallback(
    (img: AnyImage) => {
      if (img?.id) {
        toggleFavourite(String(img.id));
      }
    },
    [toggleFavourite],
  );

  const handleShareImage = useCallback(async (img: AnyImage) => {
    const shareUrl = img.url || img.path;
    const shareTitle = img.name || img.filename || 'Image';
    try {
      if (typeof navigator !== 'undefined' && navigator.share && shareUrl) {
        await navigator.share({ title: shareTitle, url: shareUrl });
      } else if (
        typeof navigator !== 'undefined' &&
        navigator.clipboard &&
        shareUrl
      ) {
        await navigator.clipboard.writeText(shareUrl);
        console.info('Image link copied to clipboard.');
      } else {
        console.info('Share is not supported in this environment.');
      }
    } catch (err) {
      console.error('Failed to share image:', err);
    }
  }, []);

  const renderActionButtons = (img: AnyImage) => (
    <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
      <Button
        variant="ghost"
        size="icon"
        className={`cursor-pointer rounded-full p-2.5 text-white transition-all duration-300 ${
          img.isFavourite
            ? 'bg-rose-500/80 hover:bg-rose-600 hover:shadow-lg'
            : 'bg-black/50 hover:bg-black/70 hover:shadow-lg'
        }`}
        onClick={(e) => {
          e.stopPropagation();
          handleToggleFavourite(img);
        }}
      >
        <Heart className="h-4 w-4" fill={img.isFavourite ? 'currentColor' : 'none'} />
        <span className="sr-only">Favourite</span>
      </Button>

      <Button
        variant="ghost"
        size="icon"
        className="cursor-pointer rounded-full bg-black/50 text-white hover:bg-black/70"
        onClick={(e) => {
          e.stopPropagation();
          handleShareImage(img);
        }}
        title="Share"
        aria-label="Share"
      >
        <Share2 className="h-4 w-4" />
        <span className="sr-only">Share</span>
      </Button>
    </div>
  );

  // Use chronological gallery (if present) for that mode
  if (mode === 'chronological') {
    // ChronologicalGallery exists in your repo; pass-through props
    return (
      <ChronologicalGallery
        images={images as any} // ChronologicalGallery expects your original Image type
        showTitle={true}
        title={title}
        onMonthOffsetsChange={onMonthOffsetsChange}
        scrollContainerRef={scrollableRef}
      />
    );
  }

  // GRID
  if (mode === 'grid') {
    return (
      <>
        <div className="p-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {images.map((img, index) => (
            <div
              key={String(img.id)}
              className="group relative rounded overflow-hidden border dark:border-gray-700 hover:shadow-md transition bg-white dark:bg-gray-900 cursor-pointer"
              role="button"
              tabIndex={0}
              onClick={() => handleImageClick(index)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleImageClick(index);
                }
              }}
            >
              <div className="relative">
                <img
                  src={getImageSrc(img)}
                  alt={(img.name || img.filename || String(img.id)) as string}
                  className="w-full h-36 object-cover transition-transform duration-200 group-hover:scale-105"
                  onError={(e) => {
                    (e.currentTarget as HTMLImageElement).src = '/placeholder.svg';
                  }}
                />
                <div className="absolute inset-0 bg-black/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
                {renderActionButtons(img)}
              </div>
            </div>
          ))}
        </div>
        {isImageViewOpen && <MediaView images={images as MediaImage[]} />}
      </>
    );
  }

  // LIST
  if (mode === 'list') {
    return (
      <>
        <div className="p-3 space-y-3">
          {images.map((img, index) => (
            <div
              key={String(img.id)}
              className="group flex items-center gap-4 p-2 rounded-md border dark:border-gray-700 bg-white dark:bg-gray-900 cursor-pointer"
              role="button"
              tabIndex={0}
              onClick={() => handleImageClick(index)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleImageClick(index);
                }
              }}
            >
              <div className="relative w-24 h-24 flex-shrink-0 rounded overflow-hidden bg-gray-100 dark:bg-gray-800">
                <img
                  src={getImageSrc(img)}
                  alt={(img.name || img.filename || '') as string}
                  className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                  onError={(e) => {
                    (e.currentTarget as HTMLImageElement).src = '/placeholder.svg';
                  }}
                />
                <div className="absolute inset-0 bg-black/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
                {renderActionButtons(img)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="font-medium truncate text-gray-900 dark:text-gray-100">
                  {img.name || img.filename || String(img.id)}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                  {img.date ||
                    img.metadata?.date ||
                    img.metadata?.createdAt ||
                    img.path ||
                    '—'}
                </div>
              </div>
            </div>
          ))}
        </div>
        {isImageViewOpen && <MediaView images={images as MediaImage[]} />}
      </>
    );
  }

 // MASONRY
if (mode === 'masonry') {
  return (
    <>
    <div className="p-3 columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4">
      {images.map((img, index) => (
        <div
          key={String(img.id)}
          className="group break-inside-avoid mb-4 overflow-hidden rounded shadow-sm bg-white dark:bg-gray-900 border dark:border-gray-700 cursor-pointer"
          role="button"
          tabIndex={0}
          onClick={() => handleImageClick(index)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleImageClick(index);
            }
          }}
        >
          {/* IMAGE should control the card height fully */}
          <div className="relative">
            <img
              src={getImageSrc(img)}
              alt={(img.name || img.filename || '') as string}
              className="w-full h-auto block transition-transform duration-200 group-hover:scale-[1.01]"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = '/placeholder.svg';
              }}
            />
            <div className="absolute inset-0 bg-black/30 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
            {renderActionButtons(img)}
          </div>

          {/* Info section — removed padding above image so card remains exact size */}
          <div className="px-2 py-1 text-xs flex items-center justify-between text-gray-700 dark:text-gray-200">
            <div className="truncate">{img.name || img.filename || ''}</div>
            <div className="text-xs opacity-70">
              {img.metadata?.date || img.date || ''}
            </div>
          </div>
        </div>
      ))}
    </div>
    {isImageViewOpen && <MediaView images={images as MediaImage[]} />}
    </>
  );
}


  return null;
};

export default GalleryView;
