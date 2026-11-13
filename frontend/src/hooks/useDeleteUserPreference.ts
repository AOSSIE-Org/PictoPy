import { useCallback, useState } from 'react';

const DELETE_FROM_COMPUTER_KEY = 'pictopy:deleteFromComputer';
const SKIP_DELETE_CONFIRM_KEY = 'pictopy:skipDeleteConfirmation';

// Reads storage, not React state, so a delete sees the live value rather than
// one captured at mount. A failed read counts as "off", the safer default.
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

// Anchored to the "Delete From Computer" value it was granted under, so changing
// that default brings the dialog back. A failed read never skips the dialog.
export const getSkipDeleteConfirmationPreference = (): boolean => {
  try {
    const anchor = localStorage.getItem(SKIP_DELETE_CONFIRM_KEY);
    return (
      anchor !== null && anchor === String(getDeleteFromComputerPreference())
    );
  } catch (err) {
    console.error('Failed to read delete-confirmation preference', err);
    return false;
  }
};

// Granting stores the current "Delete From Computer" value as the anchor checked
// above. Returns true if the write succeeded.
export const setSkipDeleteConfirmationPreference = (
  value: boolean,
): boolean => {
  try {
    if (value) {
      localStorage.setItem(
        SKIP_DELETE_CONFIRM_KEY,
        String(getDeleteFromComputerPreference()),
      );
    } else {
      localStorage.removeItem(SKIP_DELETE_CONFIRM_KEY);
    }
    return true;
  } catch (err) {
    console.error('Failed to save delete-confirmation preference', err);
    return false;
  }
};

// Kept in storage so Settings and the delete dialog share it across restarts.
export const useDeleteFromComputerPreference = () => {
  const [deleteFromComputer, setDeleteFromComputerState] = useState(
    getDeleteFromComputerPreference,
  );

  const setDeleteFromComputer = useCallback((value: boolean) => {
    // Persist first; only reflect it in the UI once the write actually
    // succeeds, so the switch never shows a state that wasn't saved.
    if (!setDeleteFromComputerPreference(value)) return;
    setDeleteFromComputerState(value);
    // A new default revokes "don't show again", so the next delete asks first
    // instead of running under a default the user never confirmed.
    setSkipDeleteConfirmationPreference(false);
  }, []);

  return { deleteFromComputer, setDeleteFromComputer };
};

export default useDeleteFromComputerPreference;
