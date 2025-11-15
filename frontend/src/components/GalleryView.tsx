// src/components/GalleryView.tsx

import { useSelector } from 'react-redux';
import { convertFileSrc } from '@tauri-apps/api/core';
import { RootState } from '@/app/store';
import { ChronologicalGallery, MonthMarker } from '@/components/Media/ChronologicalGallery';
import type { Image as MediaImage } from '@/types/Media';

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
  const mode = useSelector((s: RootState) => s.viewMode.mode);

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
      <div className="p-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {images.map((img) => (
          <div
            key={String(img.id)}
            className="relative rounded overflow-hidden border dark:border-gray-700 hover:shadow-md transition bg-white dark:bg-gray-900"
          >
            <img
              src={getImageSrc(img)}
              alt={(img.name || img.filename || String(img.id)) as string}
              className="w-full h-36 object-cover"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = '/placeholder.svg';
              }}
            />
          </div>
        ))}
      </div>
    );
  }

  // LIST
  if (mode === 'list') {
    return (
      <div className="p-3 space-y-3">
        {images.map((img) => (
          <div
            key={String(img.id)}
            className="flex items-center gap-4 p-2 rounded-md border dark:border-gray-700 bg-white dark:bg-gray-900"
          >
            <div className="w-24 h-24 flex-shrink-0 rounded overflow-hidden bg-gray-100 dark:bg-gray-800">
              <img
                src={getImageSrc(img)}
                alt={(img.name || img.filename || '') as string}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).src = '/placeholder.svg';
                }}
              />
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
    );
  }

 // MASONRY
if (mode === 'masonry') {
  return (
    <div className="p-3 columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4">
      {images.map((img) => (
        <div
          key={String(img.id)}
          className="break-inside-avoid mb-4 overflow-hidden rounded shadow-sm bg-white dark:bg-gray-900 border dark:border-gray-700"
        >
          {/* IMAGE should control the card height fully */}
          <img
            src={getImageSrc(img)}
            alt={(img.name || img.filename || '') as string}
            className="w-full h-auto block"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).src = '/placeholder.svg';
            }}
          />

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
  );
}


  return null;
};

export default GalleryView;
