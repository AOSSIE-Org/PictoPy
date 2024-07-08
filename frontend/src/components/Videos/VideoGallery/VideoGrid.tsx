import VideoCard from "./VideoCard";

import { VideoGridProps } from "@/types/video";

export default function VideoGrid({
  videos,
  videosPerRow,
  openVideoViewer,
}: VideoGridProps) {
  return (
    <div
      className={`grid gap-4 md:gap-6 ${
        videosPerRow === 2
          ? "grid-cols-1 sm:grid-cols-2"
          : videosPerRow === 3
          ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3"
          : "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
      }`}
    >
      {videos.map((video, index) => (
        <div
          key={video.id}
          onClick={() => openVideoViewer(index)}
          className="cursor-pointer"
        >
          <VideoCard video={video} />
        </div>
      ))}
    </div>
  );
}
