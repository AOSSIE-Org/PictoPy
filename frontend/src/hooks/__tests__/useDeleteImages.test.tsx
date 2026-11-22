import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { rootReducer } from '@/app/store';
import { useDeleteImages } from '@/hooks/useDeleteImages';
import * as imagesApi from '@/api/api-functions/images';
import { MEMORIES_QUERY_KEY } from '@/hooks/useMemories';

jest.mock('@/api/api-functions/images', () => ({
  deleteImages: jest.fn(),
}));

const deleteImages = imagesApi.deleteImages as jest.Mock;

function renderUseDeleteImages() {
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

  const rendered = renderHook(() => useDeleteImages(), { wrapper });
  return { ...rendered, invalidateSpy };
}

const memoriesKeyCalls = (spy: jest.SpyInstance) =>
  spy.mock.calls.filter(
    ([arg]) =>
      JSON.stringify(arg?.queryKey) === JSON.stringify(MEMORIES_QUERY_KEY),
  );

describe('useDeleteImages - memories cache invalidation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('invalidates the memories query when image deletion succeeds', async () => {
    deleteImages.mockResolvedValueOnce({
      success: true,
      data: { deleted_ids: ['img-1'], failed_paths: [] },
    });
    const { result, invalidateSpy } = renderUseDeleteImages();

    result.current.deleteImages({
      imageIds: ['img-1'],
      deleteFromDevice: false,
    });

    await waitFor(() => {
      expect(memoriesKeyCalls(invalidateSpy).length).toBeGreaterThan(0);
    });
  });

  it('does not invalidate the memories query when image deletion fails', async () => {
    deleteImages.mockRejectedValue(new Error('delete failed'));
    const { result, invalidateSpy } = renderUseDeleteImages();

    result.current.deleteImages({
      imageIds: ['img-1'],
      deleteFromDevice: false,
    });

    // autoInvalidateTags fires ['images'] on settle regardless of outcome.
    await waitFor(
      () => {
        expect(
          invalidateSpy.mock.calls.some(
            ([arg]) =>
              JSON.stringify(arg?.queryKey) === JSON.stringify(['images']),
          ),
        ).toBe(true);
      },
      { timeout: 3000 },
    );

    expect(memoriesKeyCalls(invalidateSpy)).toHaveLength(0);
  });
});
