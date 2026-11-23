/**
 * Formats seconds as `h:mm:ss` when over an hour, otherwise `m:ss`.
 * Negative and non-finite input (an unknown media duration reads as NaN or
 * Infinity) normalises to `0:00` rather than rendering `NaN:NaN`.
 */
export const formatDuration = (seconds: number): string => {
  const safeSeconds = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const secs = Math.floor(safeSeconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

/** Badge label: rounds to the nearest second, null when there's nothing to show. */
export const formatDurationLabel = (seconds?: number | null): string | null =>
  seconds && Number.isFinite(seconds)
    ? formatDuration(Math.round(seconds))
    : null;
