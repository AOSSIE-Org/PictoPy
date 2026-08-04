import { useCallback, useState } from 'react';

/**
 * A sort selection that survives a reload, stored per surface like the theme.
 *
 * The stored value is checked against the options currently on offer: one left
 * behind by an older build would otherwise sort the grid by nothing, with no
 * option showing as selected and no way to tell why.
 */
export function usePersistedSort<T extends string>(
  storageKey: string,
  defaultValue: T,
  allowedValues: readonly T[],
): [T, (value: T) => void] {
  const [sort, setSort] = useState<T>(() => {
    const stored = localStorage.getItem(storageKey) as T | null;
    return stored !== null && allowedValues.includes(stored)
      ? stored
      : defaultValue;
  });

  const selectSort = useCallback(
    (value: T) => {
      setSort(value);
      localStorage.setItem(storageKey, value);
    },
    [storageKey],
  );

  return [sort, selectSort];
}
