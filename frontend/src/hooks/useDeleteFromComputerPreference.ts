import { useCallback, useState } from 'react';

const DELETE_FROM_COMPUTER_KEY = 'pictopy:deleteFromComputer';
const SKIP_DELETE_CONFIRM_KEY = 'pictopy:skipDeleteConfirmation';

/**
 * Reads the current preference directly (no React state). Use this right
 * before an action that needs a guaranteed-fresh value, e.g. opening a
 * delete dialog, rather than a value captured back when a component mounted.
 * A storage read failure is treated as "off" — the safer default.
 */
export const getDeleteFromComputerPreference = (): boolean => {
  try {
    return localStorage.getItem(DELETE_FROM_COMPUTER_KEY) === 'true';
  } catch (err) {
    console.error('Failed to read "Delete From Computer" preference', err);
    return false;
  }
};

/** Returns true if the write succeeded. */
export const setDeleteFromComputerPreference = (value: boolean): boolean => {
  try {
    localStorage.setItem(DELETE_FROM_COMPUTER_KEY, String(value));
    return true;
  } catch (err) {
    console.error('Failed to save "Delete From Computer" preference', err);
    return false;
  }
};

/**
 * Whether the delete confirmation dialog should be skipped entirely — set by
 * checking "Don't show again" once. When true, deletes go straight through
 * using getDeleteFromComputerPreference() with no dialog shown. A storage
 * read failure is treated as "off" so a delete is never silently skipped.
 */
export const getSkipDeleteConfirmationPreference = (): boolean => {
  try {
    return localStorage.getItem(SKIP_DELETE_CONFIRM_KEY) === 'true';
  } catch (err) {
    console.error('Failed to read delete-confirmation preference', err);
    return false;
  }
};

/** Returns true if the write succeeded. */
export const setSkipDeleteConfirmationPreference = (
  value: boolean,
): boolean => {
  try {
    localStorage.setItem(SKIP_DELETE_CONFIRM_KEY, String(value));
    return true;
  } catch (err) {
    console.error('Failed to save delete-confirmation preference', err);
    return false;
  }
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
    // Persist first; only reflect it in the UI once the write actually
    // succeeds, so the switch never shows a state that wasn't saved.
    if (!setDeleteFromComputerPreference(value)) return;
    setDeleteFromComputerState(value);
    // Changing the global default is exactly the moment the per-photo
    // promise ("you can still override this per photo") needs to be
    // restored: clear any earlier "don't show again" so the next delete
    // shows the confirmation dialog again instead of deleting silently
    // under a default the user never actually confirmed.
    setSkipDeleteConfirmationPreference(false);
  }, []);

  return { deleteFromComputer, setDeleteFromComputer };
};

export default useDeleteFromComputerPreference;
