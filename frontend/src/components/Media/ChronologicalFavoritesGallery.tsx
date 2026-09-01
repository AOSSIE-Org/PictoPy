import { useMemo, useRef, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { VideoCard } from '@/components/Media/VideoCard';
import { MEDIA_GRID_CLASS } from '@/constants/layout';
import { cn } from '@/lib/utils';
import { Image, Video } from '@/types/Media';
import { groupImagesByYearMonthFromMetadata } from '@/utils/dateUtils';
import { MonthMarker } from './ChronologicalGallery';
import { setCurrentViewIndex as setCurrentImageViewIndex } from '@/features/imageSlice';
import { setCurrentViewIndex as setCurrentVideoViewIndex } from '@/features/videoSlice';
import { selectIsImageViewOpen } from '@/features/imageSelectors';
import { selectIsVideoViewOpen } from '@/features/videoSelectors';
import { MediaView } from './MediaView';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';

type FavoriteMediaItem =
  | ({ mediaType: 'image' } & Image)
  | ({ mediaType: 'video' } & Video);

type ChronologicalFavoritesGalleryProps = {
  images: Image[];
  videos: Video[];
  showTitle?: boolean;
  title?: string;
  titleRight?: React.ReactNode;
  className?: string;
  onMonthOffsetsChange?: (markers: MonthMarker[]) => void;
  scrollContainerRef?: React.RefObject<HTMLElement | null>;
};

export const ChronologicalFavoritesGallery = ({
  images,
  videos,
  showTitle = false,
  title = 'Favorites',
  titleRight,
  className = '',
  onMonthOffsetsChange,
  scrollContainerRef,
}: ChronologicalFavoritesGalleryProps) => {
  const dispatch = useDispatch();
  const monthHeaderRefs = useRef<Map<string, HTMLDivElement | null>>(new Map());
  const galleryRef = useRef<HTMLDivElement>(null);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const isVideoViewOpen = useSelector(selectIsVideoViewOpen);

  const merged = useMemo<FavoriteMediaItem[]>(
    () => [
      ...images.map((image) => ({ ...image, mediaType: 'image' as const })),
      ...videos.map((video) => ({ ...video, mediaType: 'video' as const })),
    ],
    [images, videos],
  );

  const grouped = useMemo(
    () => groupImagesByYearMonthFromMetadata(merged),
    [merged],
  );

  const sortedGrouped = useMemo(() => {
    return Object.entries(grouped)
      .sort((a, b) => Number(b[0]) - Number(a[0]))
      .map(([year, months]) => ({
        year,
        months: Object.entries(months).sort(
          (a, b) => Number(b[0]) - Number(a[0]),
        ),
      }));
  }, [grouped]);

  const chronologicallySortedItems = useMemo(() => {
    return sortedGrouped.flatMap(({ months }) =>
      months.flatMap(([, items]) => items),
    );
  }, [sortedGrouped]);

  // MediaView/VideoPlayerOverlay each navigate within their own media type,
  // so the index passed to them must be within the type-filtered sequence,
  // not the merged one.
  const chronologicallySortedImages = useMemo(
    () =>
      chronologicallySortedItems.filter(
        (item): item is FavoriteMediaItem & { mediaType: 'image' } =>
          item.mediaType === 'image',
      ),
    [chronologicallySortedItems],
  );

  const chronologicallySortedVideos = useMemo(
    () =>
      chronologicallySortedItems.filter(
        (item): item is FavoriteMediaItem & { mediaType: 'video' } =>
          item.mediaType === 'video',
      ),
    [chronologicallySortedItems],
  );

  const imageIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    chronologicallySortedImages.forEach((img, idx) => {
      map.set(img.id, idx);
    });
    return map;
  }, [chronologicallySortedImages]);

  const videoIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    chronologicallySortedVideos.forEach((video, idx) => {
      map.set(video.id, idx);
    });
    return map;
  }, [chronologicallySortedVideos]);

  const recomputeMarkers = useCallback(() => {
    if (!onMonthOffsetsChange) return;
    if (monthHeaderRefs.current.size === 0) {
      onMonthOffsetsChange([]);
      return;
    }

    const scroller = scrollContainerRef?.current;
    const scrollerTop = scroller ? scroller.getBoundingClientRect().top : 0;

    const entries = Array.from(monthHeaderRefs.current.entries()).flatMap(
      ([key, el]) => {
        if (!el) return [];
        const [y, m] = key.split('-');
        const monthName = new Date(Number(y), Number(m) - 1).toLocaleString(
          'default',
          { month: 'long' },
        );
        const offset = scroller
          ? el.getBoundingClientRect().top - scrollerTop + scroller.scrollTop
          : el.offsetTop;
        return [{ offset, month: monthName, year: y }];
      },
    );
    entries.sort((a, b) => a.offset - b.offset);
    onMonthOffsetsChange(entries);
  }, [onMonthOffsetsChange, scrollContainerRef]);

  useEffect(() => {
    recomputeMarkers();
  }, [merged, recomputeMarkers]);

  useEffect(() => {
    const elementToObserve = scrollContainerRef?.current ?? galleryRef.current;
    if (!elementToObserve) return;

    const observer = new ResizeObserver(recomputeMarkers);

    observer.observe(elementToObserve);

    return () => {
      observer.disconnect();
    };
  }, [recomputeMarkers, scrollContainerRef]);

  return (
    <>
      <div ref={galleryRef} className={`space-y-0 ${className}`}>
        {/* Title */}
        {showTitle && (
          <div className="mt-6 mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-bold">{title}</h1>
            {titleRight && <div>{titleRight}</div>}
          </div>
        )}

        {/* Gallery Content */}
        {sortedGrouped.map(({ year, months }) => (
          <div key={year} data-year={year}>
            {months.map(([month, items]) => {
              const monthName = new Date(
                Number(year),
                Number(month) - 1,
              ).toLocaleString('default', { month: 'long' });

              return (
                <div
                  key={`${year}-${month}`}
                  className="mb-8"
                  data-timeline-month={`${year}-${month}`}
                  id={`timeline-section-${year}-${month}`}
                  ref={(el) => {
                    const key = `${year}-${month}`;
                    if (el) {
                      monthHeaderRefs.current.set(key, el);
                    } else {
                      monthHeaderRefs.current.delete(key);
                    }
                  }}
                >
                  {/* Sticky Month/Year Header */}
                  <div className="bg-background sticky top-0 z-10 py-3 backdrop-blur-sm">
                    <h3 className="flex items-center text-xl font-semibold text-gray-800 dark:text-gray-200">
                      <div className="bg-primary mr-2 h-6 w-1"></div>
                      {monthName} {year}
                      <div className="mt-1 ml-2 text-sm font-normal text-gray-500">
                        {items.length} {items.length === 1 ? 'item' : 'items'}
                      </div>
                    </h3>
                  </div>

                  {/* Media Grid */}
                  <div className={cn(MEDIA_GRID_CLASS, 'p-2')}>
                    {items.map((item) =>
                      item.mediaType === 'image' ? (
                        <div key={item.id} className="group relative">
                          <ImageCard
                            image={item}
                            onClick={() =>
                              dispatch(
                                setCurrentImageViewIndex(
                                  imageIndexMap.get(item.id) ?? -1,
                                ),
                              )
                            }
                            className="w-full transition-transform duration-200 group-hover:scale-105"
                          />
                        </div>
                      ) : (
                        <div key={item.id} className="group relative">
                          <VideoCard
                            video={item}
                            onClick={() =>
                              dispatch(
                                setCurrentVideoViewIndex(
                                  videoIndexMap.get(item.id) ?? -1,
                                ),
                              )
                            }
                            className="w-full transition-transform duration-200 group-hover:scale-105"
                          />
                        </div>
                      ),
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
      {isImageViewOpen && <MediaView images={chronologicallySortedImages} />}
      {isVideoViewOpen && (
        <VideoPlayerOverlay videos={chronologicallySortedVideos} />
      )}
    </>
  );
};
