import { BACKED_URL } from '@/Config/Backend';
import { Album } from '@/types/Album';

import { useState, useCallback, useEffect } from 'react';

const apiCall = async (url: string, method: string, body?: any) => {
  let response = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const jsonResponse = await response.json();
  if (!response.ok) {
    throw new Error(
      `API call failed: ${jsonResponse.error || response.statusText}`,
    );
  }

  return jsonResponse;
};

export const useCreateAlbum = () => {
  const [isLoading, setIsLoading] = useState(false);

  const createAlbum = useCallback(
    async (newAlbum: { name: string; description?: string }) => {
      setIsLoading(true);
      try {
        const result = await apiCall(
          `${BACKED_URL}/albums/create-album`,
          'POST',
          newAlbum,
        );
        setIsLoading(false);
        return result;
      } catch (err) {
        setIsLoading(false);
        throw err;
      }
    },
    [],
  );

  return { createAlbum, isLoading, setIsLoading };
};

export const useDeleteAlbum = () => {
  const [isLoading, setIsLoading] = useState(false);

  const deleteAlbum = useCallback(async (albumId: string) => {
    setIsLoading(true);
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
      setIsLoading(false);
      throw err;
    }
  }, []);

  return { deleteAlbum, isLoading };
};

export const useAllAlbums = () => {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchAlbums = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await apiCall(`${BACKED_URL}/albums/view-all`, 'GET');
      setAlbums(result.albums);
      setIsLoading(false);
    } catch (err) {
      setIsLoading(false);
      throw err;
    }
  }, []);

  useEffect(() => {
    fetchAlbums();
  }, [fetchAlbums]);

  return { albums, isLoading, refetch: fetchAlbums };
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

  const editDescription = useCallback(
    async (albumName: string, newDescription: string) => {
      setIsLoading(true);
      try {
        const result = await apiCall(
          `${BACKED_URL}/albums/edit-album-description`,
          'PUT',
          { album_name: albumName, description: newDescription },
        );
        setIsLoading(false);
        return result;
      } catch (err) {
        setIsLoading(false);
        throw err;
      }
    },
    [],
  );

  return { editDescription, isLoading };
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
