import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { rootReducer } from '@/app/store';
import { useFolderOperations } from '@/hooks/useFolderOperations';
import * as foldersApi from '@/api/api-functions/folders';

jest.mock('@/api/api-functions/folders', () => ({
  getAllFolders: jest
    .fn()
    .mockResolvedValue({ success: true, data: { folders: [] } }),
  getFoldersTaggingStatus: jest
    .fn()
    .mockResolvedValue({ success: true, data: [] }),
  addFolder: jest.fn(),
  enableAITagging: jest.fn(),
  disableAITagging: jest.fn(),
  deleteFolders: jest.fn(),
}));

const deleteFolders = foldersApi.deleteFolders as jest.Mock;

function renderUseFolderOperations() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity, staleTime: Infinity },
      mutations: { retry: false },
    },
  });
  const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');
  const store = configureStore({ reducer: rootReducer });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </Provider>
  );

  const rendered = renderHook(() => useFolderOperations(), { wrapper });
  return { ...rendered, invalidateSpy };
}

const clustersKeyCalls = (spy: jest.SpyInstance) =>
  spy.mock.calls.filter(
    ([arg]) => JSON.stringify(arg?.queryKey) === JSON.stringify(['clusters']),
  );

describe('useFolderOperations - delete folder cache invalidation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('invalidates the clusters query when folder deletion succeeds', async () => {
    deleteFolders.mockResolvedValueOnce({ success: true, data: {} });
    const { result, invalidateSpy } = renderUseFolderOperations();

    result.current.deleteFolder('folder-1');

    await waitFor(() => {
      expect(clustersKeyCalls(invalidateSpy).length).toBeGreaterThan(0);
    });
  });

  it('does not invalidate the clusters query when folder deletion fails', async () => {
    // usePictoMutation hardcodes retry: 2, so every attempt (not just the
    // first) must reject -- otherwise the retry falls through to the mock's
    // default undefined return, which resolves as a false success.
    deleteFolders.mockRejectedValue(new Error('delete failed'));
    const { result, invalidateSpy } = renderUseFolderOperations();

    result.current.deleteFolder('folder-1');

    // autoInvalidateTags still fires ['folders'] on settle regardless of
    // outcome, so wait for that instead of an arbitrary timeout to know the
    // mutation has actually settled before asserting clusters was skipped.
    // retry: 2 with a 500ms retryDelay means settling can take >1s.
    await waitFor(
      () => {
        expect(
          invalidateSpy.mock.calls.some(
            ([arg]) =>
              JSON.stringify(arg?.queryKey) === JSON.stringify(['folders']),
          ),
        ).toBe(true);
      },
      { timeout: 3000 },
    );

    expect(clustersKeyCalls(invalidateSpy)).toHaveLength(0);
  });
});
