import { useMemo, useRef, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { VideoCard } from '@/components/Media/VideoCard';
import { Video } from '@/types/Media';
import { groupImagesByYearMonthFromMetadata } from '@/utils/dateUtils';
import { MonthMarker } from './ChronologicalGallery';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';
import { setCurrentViewIndex } from '@/features/videoSlice';
import { selectIsVideoViewOpen } from '@/features/videoSelectors';

type ChronologicalVideoGalleryProps = {
  videos: Video[];
  showTitle?: boolean;
  title?: string;
  titleRight?: React.ReactNode;
  className?: string;
  onMonthOffsetsChange?: (markers: MonthMarker[]) => void;
  scrollContainerRef?: React.RefObject<HTMLElement | null>;
};

export const ChronologicalVideoGallery = ({
  videos,
  showTitle = false,
  title = 'Video Gallery',
  titleRight,
  className = '',
  onMonthOffsetsChange,
  scrollContainerRef,
}: ChronologicalVideoGalleryProps) => {
  const dispatch = useDispatch();
  const monthHeaderRefs = useRef<Map<string, HTMLDivElement | null>>(new Map());
  const galleryRef = useRef<HTMLDivElement>(null);
  const isVideoViewOpen = useSelector(selectIsVideoViewOpen);

  const grouped = useMemo(
    () => groupImagesByYearMonthFromMetadata(videos),
    [videos],
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

  // Flatten into the same chronological order shown, so the overlay's
  // prev/next navigation matches the on-screen sequence.
  const chronologicallySortedVideos = useMemo(() => {
    return sortedGrouped.flatMap(({ months }) =>
      months.flatMap(([, vids]) => vids),
    );
  }, [sortedGrouped]);

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
  }, [videos, recomputeMarkers]);

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
          {months.map(([month, vids]) => {
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
                      {vids.length} {vids.length === 1 ? 'video' : 'videos'}
                    </div>
                  </h3>
                </div>

                {/* Videos Grid */}
                <div className="grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4 p-2">
                  {vids.map((video) => {
                    const chronologicalIndex =
                      videoIndexMap.get(video.id) ?? -1;

                    return (
                      <div key={video.id} className="group relative">
                        <VideoCard
                          video={video}
                          onClick={() =>
                            dispatch(setCurrentViewIndex(chronologicalIndex))
                          }
                          className="w-full transition-transform duration-200 group-hover:scale-105"
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ))}
      {isVideoViewOpen && (
        <VideoPlayerOverlay videos={chronologicallySortedVideos} />
      )}
    </div>
  );
};
