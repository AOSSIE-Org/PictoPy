// src/hooks/usevideos.ts

import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import { useState, useEffect } from "react";

interface VideoData {
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

export const useVideos = (folderPath: string) => {
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        console.log("Fetching videos from folder:", folderPath);

        // Fetch video paths using invoke
        const response: ResponseData = await invoke(
          "get_all_videos_with_cache",
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

        const videoUrls: VideoData[] = [];

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

            const videoPaths = response[year][month];

            const mappedVideos = await Promise.all(
              videoPaths.map(async (videoPath: string) => {
                const src = await convertFileSrc(videoPath);

                const filename = videoPath.split("\\").pop();
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
                  title: `Video ${videoPath}`,
                  date,
                  tags: [],
                };
              })
            );

            videoUrls.push(...mappedVideos);
          }
        }

        setVideos(videoUrls);
      } catch (error) {
        console.error("Error fetching videos:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, [folderPath]);

  return { videos, loading };
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
      const response = await fetch(
        "http://localhost:8000/images/multiple-images",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ paths }),
        }
      );
      console.log(response);
      if (!response.ok) {
        throw new Error("Failed to add multiple images");
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

interface Image {
  id: string;
  path: string;
  // Add other properties as needed
}

export function useFetchAllImages() {
  const [images, setImages] = useState<Image[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchImages = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/images/all-images", {
        headers: {
          accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch images");
      }
      const data = await response.json();
      console.log(data);
      setImages(data);
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
