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
  id: number;
  path: string;
  thumbnailPath: string;
  folder_id: string;
  isTagged: boolean;
  metadata?: ImageMetadata;
  isFavourite?: boolean;
  tags?: string[];
  bboxes?: { x: number; y: number; width: number; height: number }[];
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
export interface MemoryImage {
  id: number;
  path: string;
  thumbnailPath: string;
  metadata: ImageMetadata;
}

export interface Memory {
  id: string;
  title: string;
  memory_type: 'on_this_day' | 'trip' | 'date_range';
  date_range_start: string;
  date_range_end: string;
  image_count: number;
  representative_image?: MemoryImage;
  images: Image[];
  latitude?: number;
  longitude?: number;
  location_name?: string;
}

export interface Cluster {
  cluster_id: string;
  cluster_name: string;
  face_count: number;
  face_image_base64?: string;
}
