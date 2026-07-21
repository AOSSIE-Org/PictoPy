/** Formats seconds as `h:mm:ss` when over an hour, otherwise `m:ss`. */
export const formatDuration = (seconds: number): string => {
  const safeSeconds = Math.max(0, seconds);
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const secs = Math.floor(safeSeconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

/** Player clock: counts up in whole elapsed seconds, unknown reads as `0:00`. */
export const formatPlaybackTime = (seconds: number): string =>
  Number.isFinite(seconds) ? formatDuration(seconds) : '0:00';

/** Badge label: rounds to the nearest second, null when there's nothing to show. */
export const formatDurationLabel = (seconds?: number | null): string | null =>
  seconds && Number.isFinite(seconds)
    ? formatDuration(Math.round(seconds))
    : null;
