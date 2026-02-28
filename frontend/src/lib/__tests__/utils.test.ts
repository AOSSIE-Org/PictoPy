import { cn, getErrorMessage } from '../utils';

// Axios is globally mocked, so we build AxiosError-like objects manually.
function fakeAxiosError(
  message: string,
  code: string,
  responseData?: Record<string, unknown>,
) {
  return {
    isAxiosError: true,
    message,
    code,
    response: responseData ? { data: responseData } : undefined,
  };
}

/* ------------------------------------------------------------------ */
/*  cn (classname merge)                                              */
/* ------------------------------------------------------------------ */

describe('cn', () => {
  test('merges multiple class names', () => {
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2');
  });

  test('resolves Tailwind conflicts (last wins)', () => {
    expect(cn('px-4', 'px-8')).toBe('px-8');
  });

  test('handles conditional classes', () => {
    const isActive = true;
    expect(cn('base', isActive && 'active')).toBe('base active');
  });

  test('filters falsy values', () => {
    expect(cn('base', false, null, undefined, 'extra')).toBe('base extra');
  });
});

/* ------------------------------------------------------------------ */
/*  getErrorMessage                                                   */
/* ------------------------------------------------------------------ */

describe('getErrorMessage', () => {
  test('returns default message for null / undefined', () => {
    expect(getErrorMessage(null)).toBe('Something went wrong');
    expect(getErrorMessage(undefined)).toBe('Something went wrong');
  });

  test('extracts message from plain Error', () => {
    expect(getErrorMessage(new Error('disk full'))).toBe('disk full');
  });

  test('extracts response data from AxiosError', () => {
    const axiosErr = fakeAxiosError('Request failed', 'ERR_BAD_REQUEST', {
      error: 'Not Found',
      message: 'Image does not exist',
    });

    expect(getErrorMessage(axiosErr)).toBe(
      'Not Found - Image does not exist',
    );
  });

  test('falls back to code + message when response data is empty', () => {
    const axiosErr = fakeAxiosError('Network Error', 'ERR_NETWORK', {});

    expect(getErrorMessage(axiosErr)).toBe('ERR_NETWORK: Network Error');
  });

  test('handles AxiosError with no response at all', () => {
    const axiosErr = fakeAxiosError('timeout', 'ECONNABORTED');

    expect(getErrorMessage(axiosErr)).toBe('ECONNABORTED: timeout');
  });
});
