export interface ImageMetadata {
  name: string;
  date_created: string;
  width: number;
  height: number;
  file_location: string;
  file_size: number;
  item_type: string;
}

export interface Image {
  id: string;
  path: string;
  thumbnailPath: string;
  folder_id: string;
  isTagged: boolean;
  metadata?: ImageMetadata;
  tags?: string[];
  bboxes?: { x: number; y: number; width: number; height: number }[];
}
export interface ImageCardProps {
  item: Image;
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
