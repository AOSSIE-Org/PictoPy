import { useMemo, useRef, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { Image } from '@/types/Media';
import { groupImagesByYearMonthFromMetadata } from '@/utils/dateUtils';
import { setCurrentViewIndex } from '@/features/imageSlice';
import { MediaView } from './MediaView';
import { selectIsImageViewOpen } from '@/features/imageSelectors';

export type MonthMarker = {
  offset: number;
  month: string;
  year: string;
};

type ChronologicalGalleryProps = {
  images: Image[];
  showTitle?: boolean;
  title?: string;
  className?: string;
  onMonthOffsetsChange?: (markers: MonthMarker[]) => void;
  scrollContainerRef?: React.RefObject<HTMLElement | null>;
};

export const ChronologicalGallery = ({
  images,
  showTitle = false,
  title = 'Image Gallery',
  className = '',
  onMonthOffsetsChange,
  scrollContainerRef,
}: ChronologicalGalleryProps) => {
  const dispatch = useDispatch();
  const monthHeaderRefs = useRef<Map<string, HTMLDivElement | null>>(new Map());
  const galleryRef = useRef<HTMLDivElement>(null);
  const isImageViewOpen = useSelector(selectIsImageViewOpen);

  // Optimized grouping with proper date handling
  const grouped = useMemo(
    () => groupImagesByYearMonthFromMetadata(images),
    [images],
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

  const chronologicallySortedImages = useMemo(() => {
    return sortedGrouped.flatMap(({ months }) =>
      months.flatMap(([, imgs]) => imgs),
    );
  }, [sortedGrouped]);

  const imageIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    chronologicallySortedImages.forEach((img, idx) => {
      map.set(img.id, idx);
    });
    return map;
  }, [chronologicallySortedImages]);

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
  }, [images, recomputeMarkers]);

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
          <div className="mb-6">
            <h1 className="mt-6 text-2xl font-bold">{title}</h1>
          </div>
        )}

        {/* Gallery Content */}
        {sortedGrouped.map(({ year, months }) => (
          <div key={year} data-year={year}>
            {months.map(([month, imgs]) => {
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
                        {imgs.length} {imgs.length === 1 ? 'image' : 'images'}
                      </div>
                    </h3>
                  </div>

                  {/* Images Grid */}
                  <div className="grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4 p-2">
                    {imgs.map((img) => {
                      const chronologicalIndex =
                        imageIndexMap.get(img.id) ?? -1;

                      return (
                        <div key={img.id} className="group relative">
                          <ImageCard
                            image={img}
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
      </div>
      {isImageViewOpen && <MediaView images={chronologicallySortedImages} />}
    </>
  );
};
