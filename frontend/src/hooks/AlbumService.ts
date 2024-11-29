import { BACKED_URL } from '@/Config/Backend';
import { Album } from '@/types/Album';

import { useState, useCallback, useEffect } from 'react';

const apiCall = async (url: string, method: string, body?: any) => {
  const response = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }

  return response.json();
};

export const useCreateAlbum = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createAlbum = useCallback(
    async (newAlbum: { name: string; description?: string }) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiCall(
          `${BACKED_URL}/albums/create-album`,
          'POST',
          newAlbum,
        );
        setIsLoading(false);
        return result;
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error('An unknown error occurred'),
        );
        setIsLoading(false);
      }
    },
    [],
  );

  return { createAlbum, isLoading, error };
};

export const useDeleteAlbum = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const deleteAlbum = useCallback(async (albumId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiCall(
        `${BACKED_URL}/albums/delete-album`,
        'DELETE',
        {
          name: albumId,
        },
      );
      console.log(result);
      setIsLoading(false);
      return result;
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred'),
      );
      setIsLoading(false);
    }
  }, []);

  return { deleteAlbum, isLoading, error };
};

export const useAllAlbums = () => {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchAlbums = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiCall(`${BACKED_URL}/albums/view-all`, 'GET');
      setAlbums(result.albums);
      setIsLoading(false);
      console.log(result);
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred'),
      );
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlbums();
  }, [fetchAlbums]);

  return { albums, isLoading, error, refetch: fetchAlbums };
};

export const useAddImageToAlbum = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const addImage = useCallback(async (albumName: string, imagePath: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiCall(
        `${BACKED_URL}/albums/add-to-album`,
        'POST',
        {
          album_name: albumName,
          image_path: imagePath,
        },
      );
      setIsLoading(false);
      return result;
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred'),
      );
      setIsLoading(false);
    }
  }, []);

  return { addImage, isLoading, error };
};

export const useAddMultipleImagesToAlbum = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const addMultipleImages = useCallback(
    async (albumName: string, imagePaths: string[]) => {
      console.log({ album_name: albumName, image_paths: imagePaths });
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiCall(
          `${BACKED_URL}/albums/add-multiple-to-album`,
          'POST',
          { album_name: albumName, paths: imagePaths },
        );
        console.log(result);
        setIsLoading(false);
        return result;
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error('An unknown error occurred'),
        );
        setIsLoading(false);
      }
    },
    [],
  );

  return { addMultipleImages, isLoading, error };
};

export const useRemoveImageFromAlbum = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const removeImage = useCallback(
    async (albumName: string, imagePath: string) => {
      setIsLoading(true);
      setError(null);
      try {
        console.log({ album_name: albumName, path: imagePath });
        const result = await apiCall(
          `${BACKED_URL}/albums/remove-from-album`,
          'DELETE',
          { album_name: albumName, path: imagePath },
        );
        setIsLoading(false);

        return result;
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error('An unknown error occurred'),
        );
        setIsLoading(false);
      }
    },
    [],
  );

  return { removeImage, isLoading, error };
};

export const useViewAlbum = () => {
  const [album, setAlbum] = useState<Album | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const viewAlbum = useCallback(async (albumName: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiCall(
        `${BACKED_URL}/albums/view-album?album_name=${encodeURIComponent(albumName)}`,
        'GET',
      );
      setAlbum(result);
      console.log(result);
      setIsLoading(false);
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred'),
      );
      setIsLoading(false);
    }
  }, []);

  return { album, viewAlbum, isLoading, error };
};

export const useEditAlbumDescription = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const editDescription = useCallback(
    async (albumName: string, newDescription: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiCall(
          `${BACKED_URL}/albums/edit-album-description`,
          'PUT',
          { album_name: albumName, new_description: newDescription },
        );
        setIsLoading(false);
        return result;
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error('An unknown error occurred'),
        );
        setIsLoading(false);
      }
    },
    [],
  );

  return { editDescription, isLoading, error };
};

interface AddMultipleImagesResult {
  data: any | null;
  error: string | null;
  isLoading: boolean;
}

export function useAddMultipleImages() {
  const [result, setResult] = useState<AddMultipleImagesResult>({
    data: null,
    error: null,
    isLoading: false,
  });

  const addMultipleImages = async (paths: string[]): Promise<void> => {
    setResult({ data: null, error: null, isLoading: true });

    try {
      const response = await fetch(`${BACKED_URL}/images/multiple-images`, {
        method: 'POST',
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

  return { addMultipleImages, ...result };
}

// interface Image {
//   id: string;
//   path: string;
//   // Add other properties as needed
// }

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
