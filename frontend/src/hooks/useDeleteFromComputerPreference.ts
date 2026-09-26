import { useCallback, useState } from 'react';

const DELETE_FROM_COMPUTER_KEY = 'pictopy:deleteFromComputer';
const SKIP_DELETE_CONFIRM_KEY = 'pictopy:skipDeleteConfirmation';

/**
 * Reads the current preference directly (no React state). Use this right
 * before an action that needs a guaranteed-fresh value, e.g. opening a
 * delete dialog, rather than a value captured back when a component mounted.
 */
export const getDeleteFromComputerPreference = (): boolean =>
  localStorage.getItem(DELETE_FROM_COMPUTER_KEY) === 'true';

export const setDeleteFromComputerPreference = (value: boolean): void => {
  localStorage.setItem(DELETE_FROM_COMPUTER_KEY, String(value));
};

/**
 * Whether deleting a photo in PictoPy should also delete the original file
 * from disk by default. Persisted locally so it's remembered across app
 * restarts and shared between the Settings toggle and the delete dialog.
 */
export const useDeleteFromComputerPreference = () => {
  const [deleteFromComputer, setDeleteFromComputerState] = useState(
    getDeleteFromComputerPreference,
  );

  const setDeleteFromComputer = useCallback((value: boolean) => {
    setDeleteFromComputerState(value);
    setDeleteFromComputerPreference(value);
  }, []);

  return { deleteFromComputer, setDeleteFromComputer };
};

/**
 * Whether the delete confirmation dialog should be skipped entirely — set by
 * checking "Don't show again" once. When true, deletes go straight through
 * using getDeleteFromComputerPreference() with no dialog shown.
 */
export const getSkipDeleteConfirmationPreference = (): boolean =>
  localStorage.getItem(SKIP_DELETE_CONFIRM_KEY) === 'true';

export const setSkipDeleteConfirmationPreference = (value: boolean): void => {
  localStorage.setItem(SKIP_DELETE_CONFIRM_KEY, String(value));
};

export default useDeleteFromComputerPreference;
