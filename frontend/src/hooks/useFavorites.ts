import { useState, useCallback } from 'react';

export const useFavorites = () => {
  const [favorites, setFavorites] = useState<string[]>([]);
  const toggleFavorite = useCallback((imagePath: string) => {
    setFavorites((prev) => {
      const isFavorite = prev.includes(imagePath);
      if (isFavorite) {
        return prev.filter((f) => f !== imagePath);
      } else {
        return [...prev, imagePath];
      }
    });
  }, []);

  const isFavorite = useCallback(
    (imagePath: string) => {
      return favorites.includes(imagePath);
    },
    [favorites],
  );

  return {
    favorites,
    toggleFavorite,
    isFavorite,
  };
};
