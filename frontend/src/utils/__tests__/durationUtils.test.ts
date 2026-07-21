import {
  formatDuration,
  formatDurationLabel,
  formatPlaybackTime,
} from '../durationUtils';

describe('formatDuration', () => {
  test('formats minutes and seconds', () => {
    expect(formatDuration(75)).toBe('1:15');
  });

  test('formats hours with padded minutes and seconds', () => {
    expect(formatDuration(3725)).toBe('1:02:05');
  });

  test('clamps negatives to zero', () => {
    expect(formatDuration(-5)).toBe('0:00');
  });
});

describe('formatPlaybackTime', () => {
  test('floors partial seconds so the clock never runs ahead', () => {
    expect(formatPlaybackTime(2.9)).toBe('0:02');
  });

  test('falls back to 0:00 for unknown durations', () => {
    expect(formatPlaybackTime(NaN)).toBe('0:00');
    expect(formatPlaybackTime(Infinity)).toBe('0:00');
  });
});

describe('formatDurationLabel', () => {
  test('rounds to the nearest second', () => {
    expect(formatDurationLabel(74.6)).toBe('1:15');
  });

  test('returns null when there is nothing to show', () => {
    expect(formatDurationLabel(undefined)).toBeNull();
    expect(formatDurationLabel(null)).toBeNull();
    expect(formatDurationLabel(0)).toBeNull();
    expect(formatDurationLabel(Infinity)).toBeNull();
  });
});
