// src/hooks/usevideos.ts

import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import { useState, useEffect } from "react";

export const usevideos = (folderPath: string) => {
  const [videos, setvideos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchvideos = async () => {
      try {
        console.log("Fetching videos from folder:", folderPath);
        const videos: string[] = await invoke("get_all_videos_with_cache", {
          directory: folderPath,
        });

        const videosPath = await Promise.all(
            videos.map(async (videosPath) => {
            const src = await convertFileSrc(videosPath);
            return {
              src,
              original: src,
              caption: `Image ${videosPath}`,
              title: `Video ${videosPath}`,
              date: new Date().toISOString(),
              popularity: 0,
            };
          })
        );

        setvideos(videosPath);
      } catch (error) {
        console.error("Error fetching videos:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchvideos();
  }, [folderPath]);

  return { videos, loading };
};
