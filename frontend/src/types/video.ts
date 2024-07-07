export interface Video {
  id: string;
  date: string;
  title: string;
  popularity: number;
  src: string;
}

export interface VideoGridProps {
  videos: Video[];
  videosPerRow: number;
  openVideoViewer: (index: number) => void;
}

export interface VideoGalleryProps {
  videos: Video[];
  title: string | null;
}

export interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}
export interface SortingControlsProps {
  sortBy: "date" | "title" | "popularity";
  setSortBy: (value: "date" | "title" | "popularity") => void;
  videosPerRow: number;
  setVideosPerRow: (value: number) => void;
}
export interface SortingControlsProps {
  sortBy: "date" | "title" | "popularity";
  setSortBy: (value: "date" | "title" | "popularity") => void;
  videosPerRow: number;
  setVideosPerRow: (value: number) => void;
}
