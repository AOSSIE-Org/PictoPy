// File: components/Videos/VideoGallery.tsx

import { useState, useMemo } from "react";
import { sortVideos } from "@/utils/videoUtils";
import SortingControls from "./VideoGallery/SortingControls";
import PaginationControls from "./VideoGallery/Pagination";
import VideoView from "./VideoGallery/VideoView";
import VideoGrid from "./VideoGallery/VideoGrid";
import { VideoGalleryProps } from "@/types/video";


export default function VideoGallery({ videos, title }: VideoGalleryProps) {
  const [sortBy, setSortBy] = useState<"date" | "title" | "popularity">("date");
  const [videosPerRow, setVideosPerRow] = useState<number>(3);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showVideoViewer, setShowVideoViewer] = useState<boolean>(false);
  const [selectedVideoIndex, setSelectedVideoIndex] = useState<number>(0);
  const videosPerPage: number = 9;

  const sortedVideos = useMemo(
    () => sortVideos(videos, sortBy),
    [sortBy, videos]
  );

  const indexOfLastVideo = currentPage * videosPerPage;
  const indexOfFirstVideo = indexOfLastVideo - videosPerPage;
  const currentVideos = sortedVideos.slice(indexOfFirstVideo, indexOfLastVideo);
  const totalPages = Math.ceil(sortedVideos.length / videosPerPage);

  const openVideoViewer = (index: number) => {
    setSelectedVideoIndex(index);
    setShowVideoViewer(true);
  };

  const closeVideoViewer = () => {
    setShowVideoViewer(false);
  };

  return (
    <div className="dark:bg-background dark:text-foreground max-w-6xl mx-auto px-4 md:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{title}</h1>
        <SortingControls
          sortBy={sortBy}
          setSortBy={setSortBy}
          videosPerRow={videosPerRow}
          setVideosPerRow={setVideosPerRow}
        />
      </div>
      <VideoGrid
        videos={currentVideos}
        videosPerRow={videosPerRow ? videosPerRow : 0}
        openVideoViewer={openVideoViewer}
      />
      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
      {showVideoViewer && (
        <VideoView
          videos={videos.map((vid) => vid.src)}
          initialIndex={selectedVideoIndex}
          onClose={closeVideoViewer}
        />
      )}
    </div>
  );
}
