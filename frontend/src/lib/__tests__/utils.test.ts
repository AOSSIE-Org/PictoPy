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

  test('extracts plain string detail from AxiosError', () => {
    const axiosErr = fakeAxiosError('Request failed', 'ERR_BAD_REQUEST', {
      detail: 'Model not found in registry',
    });
    expect(getErrorMessage(axiosErr)).toBe('Model not found in registry');
  });

  test('does not overwrite legitimately extracted string that exactly matches fallback', () => {
    const axiosErr = fakeAxiosError('Request failed', 'ERR_BAD_REQUEST', {
      detail: 'Custom fallback string',
    });
    // Even though the extracted detail exactly matches the fallback,
    // it shouldn't fall through to Axios error details
    expect(getErrorMessage(axiosErr, 'Custom fallback string')).toBe(
      'Custom fallback string',
    );
  });

  test('extracts nested error and message from object detail in AxiosError', () => {
    const axiosErr = fakeAxiosError('Request failed', 'ERR_BAD_REQUEST', {
      detail: {
        success: false,
        error: 'Validation Error',
        message: 'Cluster name cannot be empty',
      },
    });
    expect(getErrorMessage(axiosErr)).toBe(
      'Validation Error - Cluster name cannot be empty',
    );
  });

  test('extracts joined msgs from Pydantic validation array detail in AxiosError', () => {
    const axiosErr = fakeAxiosError('Request failed', '422', {
      detail: [
        {
          loc: ['body', 'name'],
          msg: 'Field required',
          type: 'value_error.missing',
        },
        {
          loc: ['body', 'age'],
          msg: 'Must be an integer',
          type: 'type_error.integer',
        },
      ],
    });
    expect(getErrorMessage(axiosErr)).toBe(
      'Field required - Must be an integer',
    );
  });

  test('returns fallback if extracted value is not a string (type guard)', () => {
    const axiosErr = fakeAxiosError('Request failed', 'ERR_BAD_REQUEST', {
      detail: { something: 'weird' }, // neither string, nor array, nor has error/message
    });
    // With nothing matching, it falls back to Axios error details
    expect(getErrorMessage(axiosErr)).toBe('ERR_BAD_REQUEST: Request failed');
  });

  test('extracts top-level error and message from AxiosError', () => {
    const axiosErr = fakeAxiosError('Request failed', 'ERR_BAD_REQUEST', {
      error: 'Not Found',
      message: 'Image does not exist',
    });

    expect(getErrorMessage(axiosErr)).toBe('Not Found - Image does not exist');
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
