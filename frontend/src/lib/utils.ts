import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { AxiosError } from 'axios';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getErrorMessage(
  error: unknown,
  fallback: string = 'Something went wrong',
): string {
  let extracted: string | null = null;

  if (error) {
    if ((error as AxiosError).isAxiosError) {
      const axiosErr = error as AxiosError<any>;
      const resData = axiosErr.response?.data;

      if (resData) {
        if (resData.detail !== undefined) {
          if (typeof resData.detail === 'string') {
            extracted = resData.detail;
          } else if (Array.isArray(resData.detail)) {
            const msgs = resData.detail
              .map((err: any) => err?.msg)
              .filter(Boolean);
            if (msgs.length > 0) extracted = msgs.join(' - ');
          } else if (
            typeof resData.detail === 'object' &&
            resData.detail !== null
          ) {
            const detailObj = resData.detail as any;
            if (detailObj.error || detailObj.message) {
              extracted = [detailObj.error, detailObj.message]
                .filter(Boolean)
                .join(' - ');
            }
          }
        } else if (resData.error || resData.message) {
          extracted = [resData.error, resData.message]
            .filter(Boolean)
            .join(' - ');
        }

        if (extracted === null && axiosErr.message) {
          extracted = `${axiosErr.code || 'ERROR'}: ${axiosErr.message}`;
        }
      } else {
        extracted = `${axiosErr.code || 'ERROR'}: ${axiosErr.message}`;
      }
    } else if (error instanceof Error) {
      extracted = error.message;
    }
  }

  const finalResult = extracted !== null ? extracted : fallback;

  if (typeof finalResult !== 'string' || finalResult.trim() === '') {
    return fallback;
  }

  return finalResult;
}

export const formatTierLabel = (tier: string) =>
  tier.charAt(0).toUpperCase() + tier.slice(1);
