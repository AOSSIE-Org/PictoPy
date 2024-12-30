// src/hooks/usevideos.ts

import { convertFileSrc, invoke } from '@tauri-apps/api/core';
import { useState, useEffect } from 'react';

interface VideoData {
  original: string;
  url: string;
  thumbnailUrl?: string;
  date?: string;
  title?: string;
  tags?: string[];
}

interface ResponseData {
  [year: string]: {
    [month: string]: string[];
  };
}

export const useVideos = (folderPath: string) => {
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        // Fetch video paths using invoke
        const response: ResponseData = await invoke(
          'get_all_videos_with_cache',
          {
            directory: folderPath,
          },
        );

        // Ensure response is in the expected format
        if (!response || typeof response !== 'object') {
          console.error('Invalid response format:', response);
          setLoading(false);
          return;
        }

        const videoUrls: VideoData[] = [];

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

            const videoPaths = response[year][month];

            const mappedVideos = await Promise.all(
              videoPaths.map(async (videoPath: string) => {
                const original = videoPath;
                const url = await convertFileSrc(videoPath);

                const filename = videoPath.split('\\').pop();
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
                  url,
                  original,
                  title: `Video ${videoPath}`,
                  date,
                  tags: [],
                };
              }),
            );

            videoUrls.push(...mappedVideos);
          }
        }

        setVideos(videoUrls);
      } catch (error) {
        console.error('Error fetching videos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, [folderPath]);

  return { videos, loading };
};
