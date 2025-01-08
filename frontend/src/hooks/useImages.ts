// src/hooks/useImages.ts

import { convertFileSrc, invoke } from '@tauri-apps/api/core';
import { useState, useEffect } from 'react';
import { usePictoMutation } from '@/hooks/useQueryExtensio';
import { generateThumbnails } from '../../api/api-functions/images';
interface ImageData {
  original: string;
  url: string;
  thumbnailUrl: string;
  title: string;
  date: string;
  tags: string[];
  imagePath: string;
}

interface ResponseData {
  [year: string]: {
    [month: string]: string[];
  };
}

export const extractThumbnailPath = (folderPath: string, imagePath: string) => {
  const cleanedFolderPath = folderPath.replace(/\\/g, '/'); // Replaces '\' with '/'
  const thumbnailImageName = imagePath
    .replace(/\\/g, '/') // Replaces '\\' with '/'
    .replace(cleanedFolderPath + '/', '')
    .replace(/\//g, '.'); // Replaces '/' with '.'
  return `${cleanedFolderPath}/PictoPy.thumbnails/${thumbnailImageName}`;
};

export const useImages = (folderPath: string) => {
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(true);
  const { mutate: generateThumbnail, isPending: isCreating } = usePictoMutation(
    {
      mutationFn: generateThumbnails,
      autoInvalidateTags: ['ai-tagging-images', 'ai'],
    },
  );

  const fetchImages = async () => {
    try {
      // Fetch image paths using invoke
      const response: ResponseData = await invoke('get_all_images_with_cache', {
        directory: folderPath,
      });

      // Ensure response is in the expected format

      if (!response || typeof response !== 'object') {
        console.error('Invalid response format:', response);
        setLoading(false);
        return;
      }

      const imageUrls: ImageData[] = [];

      // Iterate through each year in the response
      for (const year in response) {
        if (
          !response.hasOwnProperty(year) ||
          typeof response[year] !== 'object'
        ) {
          continue;
        }

        // Iterate through each month in the current year
        for (const year in response) {
          if (
            !response.hasOwnProperty(year) ||
            typeof response[year] !== 'object'
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
                const original = imagePath;
                const fileName = imagePath.split('\\').pop();
                const url = convertFileSrc(imagePath);
                const thumbnailUrl = convertFileSrc(
                  extractThumbnailPath(folderPath, imagePath),
                );
                const matches = fileName
                  ? fileName.match(/\d{4}-\d{2}-\d{2}/)
                  : null;

                let date = null;
                if (matches) {
                  date = new Date(matches[0]).toISOString();
                } else {
                  date = new Date().toISOString(); // Default to today's date if no valid date found in filename
                }

                return {
                  original,
                  url,
                  imagePath,
                  thumbnailUrl,
                  title: `Image ${imagePath}`,
                  date,
                  tags: [],
                };
              }),
            );

            imageUrls.push(...mappedImages);
          }
        }
      }
      setImages(imageUrls);
    } catch (error) {
      console.error('Error fetching images:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('Loading true');
    generateThumbnail(folderPath);
    fetchImages();
  }, [folderPath]);

  return { images, loading, refetch: fetchImages, isCreating };
};
