export interface ImageMetadata {
  name: string;
  date_created: string | null;
  width: number;
  height: number;
  file_location: string;
  file_size: number;
  item_type: string;
  latitude?: number;
  longitude?: number;
}

export interface Image {
  id: string;
  path: string;
  thumbnailPath: string;
  folder_id: string;
  isTagged: boolean;
  metadata?: ImageMetadata;
  isFavourite?: boolean;
  tags?: string[];
  bboxes?: { x: number; y: number; width: number; height: number }[];
}

export interface ScoredImage extends Image {
  score: number;
}

export interface VideoMetadata {
  name: string;
  date_created: string | null;
  width: number;
  height: number;
  duration?: number | null;
  fps?: number | null;
  file_location: string;
  file_size: number;
  item_type: string;
}

export interface Video {
  id: string;
  path: string;
  thumbnailPath: string | null;
  folder_id: string;
  metadata?: VideoMetadata;
  isFavourite?: boolean;
  tags?: string[];
}

export interface ScoredVideo extends Video {
  score: number;
  /** Timestamp (seconds) of the keyframe that matched best. */
  best_frame_timestamp?: number | null;
}

export interface ImageGalleryProps {
  mediaItems: Image[];
  title?: string;
}

export interface ImageGridProps {
  mediaItems: Image[];
  itemsPerRow: number;
  openMediaViewer: (index: number) => void;
}
export interface MediaViewProps {
  onClose?: () => void;
  type?: string;
  images: Image[];
  onToggleFavorite?: (imageId: string) => void | Promise<void>;
}

export interface SortingControlsProps {
  sortBy: string;
  setSortBy: (value: string) => void;
  mediaItems: Image[];
}
export interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export interface Cluster {
  cluster_id: string;
  cluster_name: string;
  face_count: number;
  face_image_base64?: string;
}
