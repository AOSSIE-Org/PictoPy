// src/hooks/useImages.ts

import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import { useState, useEffect } from "react";

export const useImages = (folderPath: string) => {
  const [images, setImages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchImages = async () => {
      try {
        console.log("Fetching images from folder:", folderPath);
        const imagePaths: string[] = await invoke("get_all_images_with_cache", {
          directory: folderPath,
        });

        const imageUrls = await Promise.all(
          imagePaths.map(async (imagePath) => {
            const src = await convertFileSrc(imagePath);
            return {
              src,
              original: src,
              caption: `Image ${imagePath}`,
              title: `Video ${imagePath}`,
              date: new Date().toISOString(),
              popularity: 0,
              tags: [],
            };
          })
        );

        setImages(imageUrls);
      } catch (error) {
        console.error("Error fetching images:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchImages();
  }, [folderPath]);

  return { images, loading };
};
