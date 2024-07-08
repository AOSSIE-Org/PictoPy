import { Image } from "@/types/image";
import ImageCard from "./ImageCard";

interface ImageGridProps {
  images: Image[];
  imagesPerRow: number;
  openImageViewer: (index: number) => void;
}

export default function ImageGrid({
  images,
  imagesPerRow,
  openImageViewer,
}: ImageGridProps) {
  return (
    <div
      className={`grid gap-4 md:gap-6 ${
        imagesPerRow === 2
          ? "grid-cols-1 sm:grid-cols-2"
          : imagesPerRow === 3
          ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3"
          : "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
      }`}
    >
      {images.map((image, index) => (
        <div
          key={image.id}
          onClick={() => openImageViewer(index)}
          className="cursor-pointer"
        >
          <ImageCard image={image} />
        </div>
      ))}
    </div>
  );
}
