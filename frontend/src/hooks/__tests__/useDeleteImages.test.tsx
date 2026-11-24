import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { rootReducer } from '@/app/store';
import { deleteImages } from '@/api/api-functions/images';
import { MEMORIES_QUERY_KEY } from '@/hooks/useMemories';
import { useDeleteImages } from '@/hooks/useDeleteImages';

jest.mock('@/api/api-functions/images', () => ({
  deleteImages: jest.fn(),
}));

const mockDeleteImages = deleteImages as jest.Mock;

describe('useDeleteImages', () => {
  it('invalidates memories after deleting images', async () => {
    mockDeleteImages.mockResolvedValue({
      success: true,
      data: { deleted_ids: ['image-1'], failed_paths: [] },
    });

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');
    const store = configureStore({ reducer: rootReducer });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Provider>
    );
    const { result } = renderHook(() => useDeleteImages(), { wrapper });

    result.current.deleteImages({
      imageIds: ['image-1'],
      deleteFromDevice: false,
    });

    await waitFor(() =>
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: MEMORIES_QUERY_KEY,
      }),
    );
  });
});
