export interface Image {
  id: string;
  date: string;
  title: string;
  popularity: number;
  src: string;
}
export interface SortingControlsProps {
  sortBy: "date" | "title" | "popularity";
  setSortBy: (value: "date" | "title" | "popularity") => void;
  imagesPerRow: number;
  setImagesPerRow: (value: number) => void;
}
export interface ImageGalleryProps {
  images: Image[];
  title: string | null;
}
