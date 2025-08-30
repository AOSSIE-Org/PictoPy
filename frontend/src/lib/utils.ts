import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { AxiosError } from 'axios';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getErrorMessage(error: unknown): string {
  if (!error) return 'Something went wrong';

  // Check if error is an AxiosError
  if ((error as AxiosError).isAxiosError) {
    const axiosErr = error as AxiosError<any>;
    const resData = axiosErr.response?.data;

    // Case 1: Response exists and contains error/message fields
    if (resData && (resData.error || resData.message)) {
      return [resData.error, resData.message].filter(Boolean).join(' - ');
    }

    // Case 2: Response missing error/message, fallback to Axios error details
    return `${axiosErr.code || 'ERROR'}: ${axiosErr.message}`;
  }

  // Fallback for non-Axios errors
  return (error as Error).message || 'Something went wrong';
}
