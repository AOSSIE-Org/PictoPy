import { BACKED_URL } from '@/Config/Backend';
import { useState, useEffect } from 'react';

interface DeleteMultipleImagesResult {
  data: any | null;
  error: string | null;
  isLoading: boolean;
}

export function useDeleteMultipleImages() {
  const [result, setResult] = useState<DeleteMultipleImagesResult>({
    data: null,
    error: null,
    isLoading: false,
  });

  const deleteMultipleImages = async (paths: string[]): Promise<void> => {
    setResult({ data: null, error: null, isLoading: true });

    try {
      const response = await fetch(`${BACKED_URL}/images/multiple-images`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paths }),
      });
      console.log(response);
      if (!response.ok) {
        throw new Error('Failed to add multiple images');
      }

      const data = await response.json();
      setResult({ data, error: null, isLoading: false });
    } catch (error) {
      setResult({
        data: null,
        error: (error as Error).message,
        isLoading: false,
      });
    }
  };

  return { deleteMultipleImages, ...result };
}

export function useFetchAllImages() {
  const [images, setImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchImages = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKED_URL}/images/all-images`, {
        headers: {
          accept: 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch images');
      }
      const data = await response.json();
      console.log(data);
      setImages(data.images);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  return { images, isLoading, error, refetch: fetchImages };
}
