/**
 * Format duration from seconds to MM:SS or HH:MM:SS
 * @param seconds - Duration in seconds (can be 0)
 * @returns Formatted duration string
 */
export const formatDuration = (seconds?: number | null): string => {
  // Only return default for undefined/null, not for zero
  if (seconds === undefined || seconds === null) return '00:00';

  const totalSeconds = Math.floor(seconds);
  const hrs = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};
