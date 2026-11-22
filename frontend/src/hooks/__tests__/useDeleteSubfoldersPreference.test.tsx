import { act, renderHook } from '@testing-library/react';

import {
  getDeleteSubfoldersPreference,
  setDeleteSubfoldersPreference,
  getSkipFolderDeleteConfirmationPreference,
  setSkipFolderDeleteConfirmationPreference,
  useDeleteSubfoldersPreference,
} from '../useDeleteSubfoldersPreference';

beforeEach(() => localStorage.clear());

describe('delete subfolders preference', () => {
  it('defaults to keeping subfolders', () => {
    expect(getDeleteSubfoldersPreference()).toBe(false);
    expect(getSkipFolderDeleteConfirmationPreference()).toBe(false);
  });

  it('round-trips the value', () => {
    expect(setDeleteSubfoldersPreference(true)).toBe(true);
    expect(getDeleteSubfoldersPreference()).toBe(true);
  });

  it('treats a storage failure as "keep subfolders"', () => {
    const spy = jest
      .spyOn(Storage.prototype, 'getItem')
      .mockImplementation(() => {
        throw new Error('denied');
      });
    jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(getDeleteSubfoldersPreference()).toBe(false);
    expect(getSkipFolderDeleteConfirmationPreference()).toBe(false);

    spy.mockRestore();
    jest.restoreAllMocks();
  });
});

describe('skip folder-delete confirmation', () => {
  it('is granted for the current default', () => {
    setSkipFolderDeleteConfirmationPreference(true);
    expect(getSkipFolderDeleteConfirmationPreference()).toBe(true);
  });

  it('lapses when the default changes afterwards', () => {
    setSkipFolderDeleteConfirmationPreference(true);
    setDeleteSubfoldersPreference(true);
    expect(getSkipFolderDeleteConfirmationPreference()).toBe(false);
  });

  it('can be revoked', () => {
    setSkipFolderDeleteConfirmationPreference(true);
    setSkipFolderDeleteConfirmationPreference(false);
    expect(getSkipFolderDeleteConfirmationPreference()).toBe(false);
  });
});

describe('useDeleteSubfoldersPreference', () => {
  it('reads the stored value and saves changes', () => {
    localStorage.setItem('pictopy:deleteSubfolders', 'true');
    const { result } = renderHook(() => useDeleteSubfoldersPreference());
    expect(result.current.deleteSubfolders).toBe(true);

    act(() => result.current.setDeleteSubfolders(false));

    expect(result.current.deleteSubfolders).toBe(false);
    expect(getDeleteSubfoldersPreference()).toBe(false);
  });

  it('brings the confirmation dialog back when toggled', () => {
    setSkipFolderDeleteConfirmationPreference(true);
    const { result } = renderHook(() => useDeleteSubfoldersPreference());

    act(() => result.current.setDeleteSubfolders(true));

    expect(getSkipFolderDeleteConfirmationPreference()).toBe(false);
  });

  it('follows a change saved elsewhere, e.g. from the dialog', () => {
    const { result } = renderHook(() => useDeleteSubfoldersPreference());
    expect(result.current.deleteSubfolders).toBe(false);

    act(() => {
      setDeleteSubfoldersPreference(true);
    });

    expect(result.current.deleteSubfolders).toBe(true);
  });

  it('does not show a value that failed to save', () => {
    const { result } = renderHook(() => useDeleteSubfoldersPreference());
    const spy = jest
      .spyOn(Storage.prototype, 'setItem')
      .mockImplementation(() => {
        throw new Error('full');
      });
    jest.spyOn(console, 'error').mockImplementation(() => {});

    act(() => result.current.setDeleteSubfolders(true));

    expect(result.current.deleteSubfolders).toBe(false);
    spy.mockRestore();
    jest.restoreAllMocks();
  });
});
