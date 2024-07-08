// File: utils/videoUtils.ts

import { Video } from "@/types/video";

export function sortVideos(
  videos: Video[],
  sortBy: "date" | "title" | "popularity"
): Video[] {
  return videos.slice().sort((a, b) => {
    switch (sortBy) {
      case "date":
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      case "title":
        return a.title.localeCompare(b.title);
      case "popularity":
        return b.popularity - a.popularity;
      default:
        return 0;
    }
  });
}
