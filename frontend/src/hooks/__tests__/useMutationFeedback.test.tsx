import React from 'react';
import { renderHook } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { rootReducer } from '@/app/store';
import { useMutationFeedback } from '../useMutationFeedback';

// Mirrors MyFav.tsx: one call owns the (global, single-owner) loader for as
// long as it's pending, a second, sibling call reports errors only via
// showLoading: false and must never touch the loader either way.
const renderWithTwoFeedbackCalls = (isPending: boolean) => {
  const store = configureStore({ reducer: rootReducer });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );

  renderHook(
    () => {
      useMutationFeedback(
        { isPending },
        { loadingMessage: 'Loading', showSuccess: false, showError: false },
      );
      useMutationFeedback(
        { isSuccess: false, isError: false },
        { showLoading: false, showSuccess: false, showError: false },
      );
    },
    { wrapper },
  );

  return store;
};

describe('useMutationFeedback', () => {
  test('a showLoading:false call does not hide a loader a sibling call is showing', () => {
    const store = renderWithTwoFeedbackCalls(true);
    expect(store.getState().loader.loading).toBe(true);
  });

  test('the loader is hidden once the owning call is no longer pending', () => {
    const store = renderWithTwoFeedbackCalls(false);
    expect(store.getState().loader.loading).toBe(false);
  });

  test('calls onSuccess even when showSuccess is false', () => {
    const store = configureStore({ reducer: rootReducer });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    );
    const onSuccess = jest.fn();

    renderHook(
      () =>
        useMutationFeedback(
          { isSuccess: true },
          { showSuccess: false, onSuccess },
        ),
      { wrapper },
    );

    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(store.getState().infoDialog.isOpen).toBe(false);
  });

  test('calls onError even when showError is false', () => {
    const store = configureStore({ reducer: rootReducer });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    );
    const onError = jest.fn();
    const testError = new Error('Test error');

    renderHook(
      () =>
        useMutationFeedback(
          { isError: true, error: testError },
          { showError: false, onError },
        ),
      { wrapper },
    );

    expect(onError).toHaveBeenCalledWith(testError);
    expect(store.getState().infoDialog.isOpen).toBe(false);
  });
});
