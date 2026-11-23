import { useCallback, useSyncExternalStore } from 'react';

const DELETE_SUBFOLDERS_KEY = 'pictopy:deleteSubfolders';
const SKIP_FOLDER_DELETE_CONFIRM_KEY = 'pictopy:skipFolderDeleteConfirmation';
// Lets every mounted switch re-read after a change made elsewhere on the page
// (e.g. the folder-delete dialog saving a new default).
const CHANGE_EVENT = 'pictopy:deleteSubfolders-changed';

/**
 * Whether deleting a folder should also delete its subfolders by default.
 * Read straight from storage so callers get a fresh value right before an
 * action. Off (keep subfolders) is the default, and a storage failure also
 * counts as "off" — the safer choice.
 */
export const getDeleteSubfoldersPreference = (): boolean => {
  try {
    return localStorage.getItem(DELETE_SUBFOLDERS_KEY) === 'true';
  } catch (err) {
    console.error('Failed to read "Delete Subfolders" preference', err);
    return false;
  }
};

/** Returns true if the write succeeded. */
export const setDeleteSubfoldersPreference = (value: boolean): boolean => {
  try {
    localStorage.setItem(DELETE_SUBFOLDERS_KEY, String(value));
    window.dispatchEvent(new Event(CHANGE_EVENT));
    return true;
  } catch (err) {
    console.error('Failed to save "Delete Subfolders" preference', err);
    return false;
  }
};

/**
 * Whether the folder-delete dialog is skipped ("Don't show again"). Like the
 * photo-delete one, the skip is anchored to the "Delete Subfolders" value it
 * was granted under: if that default changes, the anchor stops matching and
 * the dialog comes back rather than deleting under a default the user never
 * confirmed. A read failure means "show the dialog".
 */
export const getSkipFolderDeleteConfirmationPreference = (): boolean => {
  try {
    const anchor = localStorage.getItem(SKIP_FOLDER_DELETE_CONFIRM_KEY);
    return (
      anchor !== null && anchor === String(getDeleteSubfoldersPreference())
    );
  } catch (err) {
    console.error('Failed to read folder-delete confirmation preference', err);
    return false;
  }
};

/** Grants (true, anchored to the current default) or revokes (false) the skip. */
export const setSkipFolderDeleteConfirmationPreference = (
  value: boolean,
): boolean => {
  try {
    if (value) {
      localStorage.setItem(
        SKIP_FOLDER_DELETE_CONFIRM_KEY,
        String(getDeleteSubfoldersPreference()),
      );
    } else {
      localStorage.removeItem(SKIP_FOLDER_DELETE_CONFIRM_KEY);
    }
    return true;
  } catch (err) {
    console.error('Failed to save folder-delete confirmation preference', err);
    return false;
  }
};

const subscribe = (onChange: () => void) => {
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => window.removeEventListener(CHANGE_EVENT, onChange);
};

/** Value + setter for the Settings switch; changing it brings the dialog back. */
export const useDeleteSubfoldersPreference = () => {
  // Read from storage, so the switch only ever shows what was actually saved.
  const deleteSubfolders = useSyncExternalStore(
    subscribe,
    getDeleteSubfoldersPreference,
  );

  const setDeleteSubfolders = useCallback((value: boolean) => {
    if (!setDeleteSubfoldersPreference(value)) return;
    setSkipFolderDeleteConfirmationPreference(false);
  }, []);

  return { deleteSubfolders, setDeleteSubfolders };
};

export default useDeleteSubfoldersPreference;
