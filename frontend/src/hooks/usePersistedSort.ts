import { useCallback, useState } from 'react';

// The stored value is checked against the options on offer: one left by an older
// build would sort the grid by nothing, with no option showing as selected.
export function usePersistedSort<T extends string>(
  storageKey: string,
  defaultValue: T,
  allowedValues: readonly T[],
): [T, (value: T) => void] {
  const [sort, setSort] = useState<T>(() => {
    // Matching against the allowed values narrows the stored string to T, so
    // no cast is needed to trust what came out of storage.
    const stored = localStorage.getItem(storageKey);
    return allowedValues.find((value) => value === stored) ?? defaultValue;
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
