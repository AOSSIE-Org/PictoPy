import { useState, useEffect, RefObject } from 'react';
import { MonthMarker } from '@/components/Media/ChronologicalGallery';

export type TooltipState = {
  top: number;
  month: string;
  year: string;
};

export function useScroll(scrollableRef: RefObject<HTMLElement | null>) {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const scrollable = scrollableRef.current;
    if (!scrollable) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollable;
      const progress = scrollTop / (scrollHeight - clientHeight);
      setScrollProgress(progress);
    };

    scrollable.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      scrollable.removeEventListener('scroll', handleScroll);
    };
  }, [scrollableRef]);

  return scrollProgress;
}

export function useWheel(
  ref: RefObject<HTMLElement | null>,
  callback: (deltaY: number) => void,
) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      callback(e.deltaY);
    };

    element.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      element.removeEventListener('wheel', handleWheel);
    };
  }, [ref, callback]);
}

export const getMarkerForScrollPosition = (
  scrollPosition: number,
  monthMarkers: MonthMarker[],
): MonthMarker | undefined => {
  return [...monthMarkers]
    .reverse()
    .find((marker) => marker.offset <= scrollPosition);
};

export const clamp = (value: number, min: number, max: number): number => {
  return Math.max(min, Math.min(value, max));
};

export const calculateClampedTooltipTop = (
  position: number,
  trackHeight: number,
  tooltipHalfHeight: number = 14,
): number => {
  return clamp(position, tooltipHalfHeight, trackHeight - tooltipHalfHeight);
};
