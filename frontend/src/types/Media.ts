export interface MediaItem {
  src: string;
  date?: string;
  title?: string;
  tags?: string[];
}
export interface MediaCardProps {
  item: MediaItem;
  type: "image" | "video";
}

export interface MediaGalleryProps {
  mediaItems: MediaItem[];
  title?: string;
  type: "image" | "video";
}

export interface MediaGridProps {
  mediaItems: MediaItem[];
  itemsPerRow: number;
  openMediaViewer: (index: number) => void;
  type: "image" | "video";
}
export interface MediaViewProps {
  initialIndex: number;
  onClose: () => void;
  allMedia: string[];
  currentPage: number;
  itemsPerPage: number;
  type: "image" | "video";
}

export interface YearOption {
  value: string;
  label: string;
}

export interface SortingControlsProps {
  sortBy: string;
  setSortBy: (value: string) => void;
  mediaItems: MediaItem[];
}
export interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}
