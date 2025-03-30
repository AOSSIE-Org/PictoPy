import { invoke, convertFileSrc } from '@tauri-apps/api/core';
import {
  extractThumbnailPath,
  ResponseData,
  ImageData,
} from '@/hooks/useImages';

export const fetchImagesForHome = async () => {
  const folderPaths = window.localStorage.getItem('folderPaths');
  if (!folderPaths || !folderPaths.length) return [];

  const parsedFolderPaths = JSON.parse(folderPaths);

  const response: ResponseData = await invoke('get_all_images_with_cache', {
    directories: parsedFolderPaths,
  });

  if (!response || typeof response !== 'object') {
    console.error('Invalid response format:', folderPaths, response);
  }
  const imageUrls: ImageData[] = [];

  for (const year in response) {
    if (!response.hasOwnProperty(year) || typeof response[year] !== 'object') {
      continue;
    }

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
          const thumbnailUrl = convertFileSrc(extractThumbnailPath(imagePath));
          const matches = fileName ? fileName.match(/\d{4}-\d{2}-\d{2}/) : null;

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
  return imageUrls;
};
