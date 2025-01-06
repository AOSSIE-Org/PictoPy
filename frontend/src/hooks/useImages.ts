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
  imagePath?: string;
}

interface ResponseData {
  [year: string]: {
    [month: string]: string[];
  };
}

export const extractThumbnailPath = (imagePath: string) => {
  const cleanedImagePath = imagePath.replace(/\\/g, '/'); // Replaces all '\' with '/'
  const thumbnailImageName = cleanedImagePath.split('/').pop() || '';
  //Extract folder path from the image path
  const folderPath = cleanedImagePath.replace(thumbnailImageName, '');
  return `${folderPath}/PictoPy.thumbnails/${thumbnailImageName}`;
};

export const useImages = (folderPaths: string[]) => {
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
      const imageUrls: ImageData[] = [];

      const response: ResponseData = await invoke('get_all_images_with_cache', {
        directories: folderPaths,
      });

      // Ensure response is in the expected format
      if (!response || typeof response !== 'object') {
        console.error('Invalid response format:', folderPaths, response);
      }

      // Iterate through each year in the response
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
              const cleanedImagePath = imagePath.replace(/\\/g, '/'); // Replaces all '\' with '/'
              const fileName = cleanedImagePath.split('/').pop();
              const url = convertFileSrc(imagePath);
              const thumbnailUrl = convertFileSrc(
                extractThumbnailPath(imagePath),
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
                thumbnailUrl,
                title: fileName || 'Untitled',
                date,
                tags: [],
              };
            }),
          );

          imageUrls.push(...mappedImages);
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
    // Generate thumbnails for all folder paths
    generateThumbnail(folderPaths);

    // Fetch images for all folder paths
    fetchImages();
  }, [folderPaths]);

  return { images, loading, refetch: fetchImages, isCreating };
};
