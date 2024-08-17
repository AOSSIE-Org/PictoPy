// src/hooks/useImages.ts

import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import { useState, useEffect } from "react";

interface ImageData {
  src: string;
  original: string;

  title: string;
  date: string;

  tags: string[];
}

interface ResponseData {
  [year: string]: {
    [month: string]: string[];
  };
}

export const useImages = (folderPath: string) => {
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchImages = async () => {
      try {
        console.log("Fetching images from folder:", folderPath);

        // Fetch image paths using invoke
        const response: ResponseData = await invoke(
          "get_all_images_with_cache",
          {
            directory: folderPath,
          }
        );

        // Ensure response is in the expected format

        if (!response || typeof response !== "object") {
          console.error("Invalid response format:", response);
          setLoading(false);
          return;
        }

        const imageUrls: ImageData[] = [];

        // Iterate through each year in the response
        for (const year in response) {
          if (
            !response.hasOwnProperty(year) ||
            typeof response[year] !== "object"
          ) {
            continue;
          }

          // Iterate through each month in the current year
          for (const month in response[year]) {
            if (
              !response[year].hasOwnProperty(month) ||
              !Array.isArray(response[year][month])
            ) {
              continue;
            }

            const imagePaths = response[year][month];

            const mappedImages = await Promise.all(
              imagePaths.map(async (imagePath: string) => {
                const src = await convertFileSrc(imagePath);

                const filename = imagePath.split("\\").pop();
                const matches = filename
                  ? filename.match(/\d{4}-\d{2}-\d{2}/)
                  : null;

                let date = null;
                if (matches) {
                  date = new Date(matches[0]).toISOString();
                } else {
                  date = new Date().toISOString(); // Default to today's date if no valid date found in filename
                }

                return {
                  src,
                  original: src,

                  title: `Image ${imagePath}`,
                  date,

                  tags: [],
                };
              })
            );

            imageUrls.push(...mappedImages);
          }
        }

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
