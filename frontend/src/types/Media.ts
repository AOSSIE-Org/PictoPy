export interface MediaItem {
  original?: string;
  url: string;
  thumbnailUrl?: string;
  date?: string;
  title?: string;
  tags?: string[];
  imagePath?: string;
}
export interface MediaCardProps {
  item: MediaItem;
  type: 'image' | 'video';
}

export interface MediaGalleryProps {
  mediaItems: MediaItem[];
  title?: string;
  type: 'image' | 'video';
}

export interface MediaGridProps {
  mediaItems: MediaItem[];
  itemsPerRow: number;
  openMediaViewer: (index: number) => void;
  type: 'image' | 'video';
}
export interface MediaViewProps {
  initialIndex: number;
  onClose: () => void;
  allMedia: { url: string; path?: string }[];
  currentPage: number;
  itemsPerPage: number;
  type: 'image' | 'video';
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
