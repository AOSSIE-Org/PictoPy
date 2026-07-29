import { useEffect, useRef, useState } from 'react';

interface UseStoryProgressOptions {
  /** Index of the slide being timed. Changing it restarts the timer. */
  index: number;
  durationMs: number;
  isPlaying: boolean;
  onComplete: () => void;
}

/**
 * Drives the segmented progress bar in the story viewer.
 *
 * Uses requestAnimationFrame rather than setInterval so the bar fills smoothly
 * and pauses resume from where they stopped instead of restarting the slide.
 * Returns progress through the current slide, 0 to 1.
 */
export const useStoryProgress = ({
  index,
  durationMs,
  isPlaying,
  onComplete,
}: UseStoryProgressOptions): number => {
  const [progress, setProgress] = useState(0);
  const elapsedRef = useRef(0);
  const frameRef = useRef<number | null>(null);
  // Kept in a ref so a new callback identity each render does not restart the
  // animation and stall the bar at zero.
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  // A new slide always starts from empty.
  useEffect(() => {
    elapsedRef.current = 0;
    setProgress(0);
  }, [index]);

  useEffect(() => {
    if (!isPlaying || durationMs <= 0) return;

    let lastTimestamp: number | null = null;
    let finished = false;

    const step = (timestamp: number) => {
      if (lastTimestamp === null) lastTimestamp = timestamp;
      elapsedRef.current += timestamp - lastTimestamp;
      lastTimestamp = timestamp;

      const next = Math.min(elapsedRef.current / durationMs, 1);
      setProgress(next);

      if (next >= 1) {
        finished = true;
        onCompleteRef.current();
        return;
      }
      frameRef.current = requestAnimationFrame(step);
    };

    frameRef.current = requestAnimationFrame(step);

    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      // Only a pause should preserve elapsed time; a completed slide is about
      // to be replaced and must not carry its timer forward.
      if (finished) elapsedRef.current = 0;
    };
  }, [index, durationMs, isPlaying]);

  return progress;
};
