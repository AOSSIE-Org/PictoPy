import { act, renderHook } from '@testing-library/react';
import { usePersistedSort } from '../usePersistedSort';

const KEY = 'test-sort';
const VALUES = ['name', 'date'] as const;
type TestSort = (typeof VALUES)[number];

const renderSort = () =>
  renderHook(() => usePersistedSort<TestSort>(KEY, 'name', VALUES));

describe('usePersistedSort', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts on the default when nothing is stored', () => {
    const { result } = renderSort();

    expect(result.current[0]).toBe('name');
  });

  it('restores the stored selection', () => {
    localStorage.setItem(KEY, 'date');

    const { result } = renderSort();

    expect(result.current[0]).toBe('date');
  });

  it('keeps the selection across a remount', () => {
    const first = renderSort();
    act(() => first.result.current[1]('date'));
    first.unmount();

    // A remount stands in for the reload that used to reset the sort.
    expect(renderSort().result.current[0]).toBe('date');
  });

  it('falls back to the default for a sort that no longer exists', () => {
    localStorage.setItem(KEY, 'photoCount');

    const { result } = renderSort();

    expect(result.current[0]).toBe('name');
  });
});
