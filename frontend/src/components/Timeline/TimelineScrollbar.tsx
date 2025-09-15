import { useEffect, useMemo, useRef, useState, RefObject } from 'react';
import {
  useScroll,
  useWheel,
  getMarkerForScrollPosition,
  TooltipState,
} from '@/utils/timelineUtils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { MonthMarker } from '@/components/Media/ChronologicalGallery';

const monthAbbreviations: Record<string, string> = {
  January: 'Jan',
  February: 'Feb',
  March: 'Mar',
  April: 'Apr',
  May: 'May',
  June: 'Jun',
  July: 'Jul',
  August: 'Aug',
  September: 'Sept',
  October: 'Oct',
  November: 'Nov',
  December: 'Dec',
};

const abbreviateMonth = (month: string) => monthAbbreviations[month] ?? month;

type TimelineScrollbarProps = {
  className?: string;
  scrollableRef: RefObject<HTMLElement | null>;
  monthMarkers?: MonthMarker[];
};

export default function TimelineScrollbar({
  className = '',
  scrollableRef,
  monthMarkers = [],
}: TimelineScrollbarProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [trackHeight, setTrackHeight] = useState<number>(0);
  const [isDragging, setIsDragging] = useState(false);
  const [isMarkerHovered, setIsMarkerHovered] = useState(false);
  const [trackTooltip, setTrackTooltip] = useState<TooltipState | null>(null);
  const [isTrackTooltipVisible, setIsTrackTooltipVisible] = useState(false);
  const [scrollTooltip, setScrollTooltip] = useState<TooltipState | null>(null);
  const [isScrollTooltipVisible, setIsScrollTooltipVisible] = useState(false);
  const [dragTooltip, setDragTooltip] = useState<
    (TooltipState & { visible: boolean }) | null
  >(null);
  const scrollProgress = useScroll(scrollableRef);
  const scrollTooltipTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [scrollableDimensions, setScrollableDimensions] = useState({
    scrollHeight: 0,
    clientHeight: 0,
  });

  useEffect(() => {
    const scrollable = scrollableRef.current;
    if (!scrollable) return;

    const measure = () => {
      setScrollableDimensions({
        scrollHeight: scrollable.scrollHeight,
        clientHeight: scrollable.clientHeight,
      });
    };

    const resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(scrollable);

    measure(); // Initial measurement

    return () => resizeObserver.disconnect();
  }, [scrollableRef]);

  const markerPositions = useMemo(() => {
    if (!scrollableRef.current || !monthMarkers.length) {
      return [];
    }

    const { scrollHeight, clientHeight } = scrollableDimensions;
    const scrollableHeight = scrollHeight - clientHeight;

    // Filter out markers that can't reach the top of the viewport
    const visibleMarkers = monthMarkers.filter(
      (marker) => marker.offset <= scrollableHeight,
    );

    const safeDenominator = Math.max(1, scrollableHeight);
    const maxTop = trackHeight;

    return visibleMarkers.map((marker) => {
      const markerTop = (marker.offset / safeDenominator) * trackHeight;
      return {
        ...marker,
        markerTop: Math.max(0, Math.min(markerTop, maxTop)),
      };
    });
  }, [monthMarkers, trackHeight, scrollableDimensions, scrollableRef]);

  useWheel(containerRef, (deltaY) => {
    const scroller = scrollableRef.current;
    if (scroller) scroller.scrollTop += deltaY;
  });

  // Effect to show/hide scroll tooltip
  useEffect(() => {
    if (isDragging || isMarkerHovered || !scrollableRef.current) {
      setIsScrollTooltipVisible(false);
      return;
    }

    if (scrollTooltipTimer.current) {
      clearTimeout(scrollTooltipTimer.current);
    }

    const scrollable = scrollableRef.current;
    const currentMarker = getMarkerForScrollPosition(
      scrollable.scrollTop,
      monthMarkers,
    );

    if (currentMarker) {
      const tooltipHalfHeight = 14;
      const top = Math.max(
        tooltipHalfHeight,
        Math.min(scrollProgress * trackHeight, trackHeight - tooltipHalfHeight),
      );

      setScrollTooltip({
        top,
        month: currentMarker.month,
        year: currentMarker.year,
      });
      setIsScrollTooltipVisible(true);
    }

    scrollTooltipTimer.current = setTimeout(() => {
      setIsScrollTooltipVisible(false);
    }, 1000);

    return () => {
      if (scrollTooltipTimer.current) {
        clearTimeout(scrollTooltipTimer.current);
      }
    };
  }, [
    scrollProgress,
    isDragging,
    isMarkerHovered,
    monthMarkers,
    scrollableRef,
    trackHeight,
  ]);

  // Measure parent height dynamically
  useEffect(() => {
    if (!containerRef.current?.parentElement) return;

    const parent = containerRef.current.parentElement;
    const measure = () => setTrackHeight(parent.clientHeight);

    measure();

    const resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(parent);

    window.addEventListener('resize', measure);
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', measure);
    };
  }, []);

  const handleScroll = (clientY: number) => {
    if (!scrollableRef.current || !trackRef.current) return;

    const { top, height } = trackRef.current.getBoundingClientRect();
    const clickY = clientY - top;
    const scrollPercentage = Math.min(Math.max(clickY / height, 0), 1);

    const scrollable = scrollableRef.current;
    const scrollToY =
      scrollPercentage * (scrollable.scrollHeight - scrollable.clientHeight);

    scrollable.scrollTo({
      top: scrollToY,
      behavior: 'auto',
    });
  };

  const updateDragTooltip = (clientY: number) => {
    if (!trackRef.current || !scrollableRef.current || !monthMarkers.length)
      return;

    const { top, height } = trackRef.current.getBoundingClientRect();
    const dragY = clientY - top;

    const scrollable = scrollableRef.current;
    const scrollPercentage = Math.min(Math.max(dragY / height, 0), 1);
    const correspondingScrollTop =
      scrollPercentage * (scrollable.scrollHeight - scrollable.clientHeight);

    const draggedMarker = getMarkerForScrollPosition(
      correspondingScrollTop,
      monthMarkers,
    );

    if (draggedMarker) {
      const tooltipHalfHeight = 14;
      const clampedDragY = Math.max(
        tooltipHalfHeight,
        Math.min(dragY, height - tooltipHalfHeight),
      );
      setDragTooltip({
        visible: true,
        top: clampedDragY,
        month: draggedMarker.month,
        year: draggedMarker.year,
      });
    }
  };

  const handleMarkerClick = (offset: number) => {
    if (!scrollableRef.current) return;

    scrollableRef.current.scrollTo({
      top: offset,
      behavior: 'smooth',
    });
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    document.body.classList.add('no-select');
    handleScroll(e.clientY);
    updateDragTooltip(e.clientY);

    const handleMouseMove = (e: MouseEvent) => {
      try {
        handleScroll(e.clientY);
        updateDragTooltip(e.clientY);
      } catch (error) {
        console.error('Error during drag:', error);
        handleMouseUp();
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.body.classList.remove('no-select');
      setDragTooltip(null);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('blur', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('blur', handleMouseUp);
  };

  const handleTrackMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDragging || isMarkerHovered) {
      setIsTrackTooltipVisible(false);
      return;
    }

    if (!trackRef.current) return;
    const { clientY } = e;
    const { top, height } = trackRef.current.getBoundingClientRect();
    const hoverY = clientY - top;

    const scrollable = scrollableRef.current;
    if (!scrollable) return;

    const scrollPercentage = Math.min(Math.max(hoverY / height, 0), 1);
    const correspondingScrollTop =
      scrollPercentage * (scrollable.scrollHeight - scrollable.clientHeight);

    const hoveredMarker = getMarkerForScrollPosition(
      correspondingScrollTop,
      monthMarkers,
    );

    if (hoveredMarker) {
      const tooltipHalfHeight = 14;
      const top = Math.max(
        tooltipHalfHeight,
        Math.min(hoverY, height - tooltipHalfHeight),
      );
      setTrackTooltip({
        top,
        month: hoveredMarker.month,
        year: hoveredMarker.year,
      });
      setIsTrackTooltipVisible(true);
    } else {
      setIsTrackTooltipVisible(false);
    }
  };

  const handleTrackMouseLeave = () => {
    setIsTrackTooltipVisible(false);
  };

  const tooltipBaseClass =
    'text-primary-foreground bg-primary absolute left-[-75px] rounded-md px-2 py-1 text-xs shadow-md';

  return (
    <div
      ref={containerRef}
      className={`absolute top-0 right-0 z-40 flex items-start justify-center ${className}`}
      style={{ height: trackHeight }}
    >
      {/* Timeline Track */}
      <div
        ref={trackRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleTrackMouseMove}
        onMouseLeave={handleTrackMouseLeave}
        className="relative w-6 cursor-row-resize rounded-full bg-gray-200 shadow-sm transition-shadow hover:shadow-md"
        style={{ height: trackHeight }}
      >
        {/* Timeline Background Gradient */}
        <div
          className="absolute inset-0 rounded-full opacity-20"
          style={{
            background: 'linear-gradient(to bottom, #3b82f6, #8b5cf6, #ec4899)',
          }}
        />

        {/* Progress Fill */}
        <div
          className="absolute top-0 left-1/2 w-full rounded-full bg-blue-400"
          style={{
            height: `${scrollProgress * trackHeight}px`,
            transform: 'translateX(-50%)',
          }}
        />

        {/* Month Markers */}
        <TooltipProvider>
          {markerPositions.map((marker, index) => {
            return (
              <Tooltip key={index}>
                <TooltipTrigger asChild>
                  <div
                    className="absolute left-1/2 h-0.5 w-full bg-gray-500 shadow-md"
                    style={{
                      top: `${marker.markerTop}px`,
                      transform: 'translate(-50%, -50%)',
                      pointerEvents: isDragging ? 'none' : 'auto',
                    }}
                    onClick={() => handleMarkerClick(marker.offset)}
                    onMouseEnter={() => !isDragging && setIsMarkerHovered(true)}
                    onMouseLeave={() => setIsMarkerHovered(false)}
                  />
                </TooltipTrigger>
                <TooltipContent side="left">
                  <p>{`${marker.month} ${marker.year}`}</p>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </TooltipProvider>

        {/* Track Hover Tooltip */}
        {trackTooltip && (
          <div
            className={`${tooltipBaseClass} transition-opacity duration-200 ${
              isTrackTooltipVisible ? 'opacity-100' : 'opacity-0'
            }`}
            style={{
              top: `${trackTooltip.top}px`,
              transform: 'translateY(-50%)',
              pointerEvents: 'none',
            }}
          >
            {`${abbreviateMonth(trackTooltip.month)} ${trackTooltip.year}`}
          </div>
        )}

        {/* Scroll Tooltip */}
        {scrollTooltip && !isTrackTooltipVisible && (
          <div
            className={`${tooltipBaseClass} transition-opacity duration-500 ${
              isScrollTooltipVisible ? 'opacity-100' : 'opacity-0'
            }`}
            style={{
              top: `${scrollTooltip.top}px`,
              transform: 'translateY(-50%)',
              pointerEvents: 'none',
            }}
          >
            {`${abbreviateMonth(scrollTooltip.month)} ${scrollTooltip.year}`}
          </div>
        )}

        {/* Drag Tooltip */}
        {isDragging && dragTooltip && dragTooltip.visible && (
          <div
            className={tooltipBaseClass}
            style={{
              top: `${dragTooltip.top}px`,
              transform: 'translateY(-50%)',
            }}
          >
            {`${abbreviateMonth(dragTooltip.month)} ${dragTooltip.year}`}
          </div>
        )}
      </div>
    </div>
  );
}
