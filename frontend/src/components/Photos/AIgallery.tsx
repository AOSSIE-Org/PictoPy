import { useState, useMemo } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { LayoutGridIcon, ListOrderedIcon } from "../Icons/Icons";
import { Button } from "../ui/button";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "../ui/pagination";

import ImageCard from "./PhotoGallery/ImageCard";
import ImageView from "./PhotoGallery/PhotosView";

interface Image {
  id: string;
  date: string;
  title: string;
  popularity: number;
  src: string;
  tags: string[];
}

interface ImageGalleryProps {
  images: Image[];
  title: string | null;
}

const classNames = [
  "person",
  "bicycle",
  "car",
  "motorcycle",
  "airplane",
  "bus",
  "train",
  "truck",
  "boat",
  "traffic light",
  "fire hydrant",
  "stop sign",
  "parking meter",
  "bench",
  "bird",
  "cat",
  "dog",
  "horse",
  "sheep",
  "cow",
  "elephant",
  "bear",
  "zebra",
  "giraffe",
  "backpack",
  "umbrella",
  "handbag",
  "tie",
  "suitcase",
  "frisbee",
  "skis",
  "snowboard",
  "sports ball",
  "kite",
  "baseball bat",
  "baseball glove",
  "skateboard",
  "surfboard",
  "tennis racket",
  "bottle",
  "wine glass",
  "cup",
  "fork",
  "knife",
  "spoon",
  "bowl",
  "banana",
  "apple",
  "sandwich",
  "orange",
  "broccoli",
  "carrot",
  "hot dog",
  "pizza",
  "donut",
  "cake",
  "chair",
  "couch",
  "potted plant",
  "bed",
  "dining table",
  "toilet",
  "tv",
  "laptop",
  "mouse",
  "remote",
  "keyboard",
  "cell phone",
  "microwave",
  "oven",
  "toaster",
  "sink",
  "refrigerator",
  "book",
  "clock",
  "vase",
  "scissors",
  "teddy bear",
  "hair drier",
  "toothbrush",
];

export default function ImageGallery({ images, title }: ImageGalleryProps) {
  const [filterTag, setFilterTag] = useState<string>("");
  const [imagesPerRow, setImagesPerRow] = useState<number>(3);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showImageViewer, setShowImageViewer] = useState<boolean>(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0);
  const imagesPerPage: number = 9;

  const filteredImages = useMemo(() => {
    return filterTag
      ? images.filter((image) => image.tags.includes(filterTag))
      : images;
  }, [filterTag, images]);

  const indexOfLastImage = currentPage * imagesPerPage;
  const indexOfFirstImage = indexOfLastImage - imagesPerPage;
  const currentImages = filteredImages.slice(
    indexOfFirstImage,
    indexOfLastImage
  );
  const totalPages = Math.ceil(filteredImages.length / imagesPerPage);

  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  };

  const openImageViewer = (index: number) => {
    setSelectedImageIndex(index);
    setShowImageViewer(true);
  };

  const closeImageViewer = () => {
    setShowImageViewer(false);
  };

  const getPageNumbers = (): (number | string)[] => {
    const maxPages = 5;
    const pages: (number | string)[] = [];

    const startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    const endPage = Math.min(totalPages, startPage + maxPages - 1);

    if (startPage > 1) {
      pages.push(1);
      if (startPage > 2) {
        pages.push("...");
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        pages.push("...");
      }
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div className="dark:bg-background dark:text-foreground max-w-6xl mx-auto px-4 md:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{title}</h1>
        <div className="flex items-center gap-4">
          {/* DropdownMenu for images per row */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                <LayoutGridIcon className="w-4 h-4" />
                {imagesPerRow} per row
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-[200px] bg-white dark:text-foreground"
              align="end"
            >
              <DropdownMenuRadioGroup
                value={imagesPerRow.toString()}
                onValueChange={(value: string) =>
                  setImagesPerRow(parseInt(value))
                }
              >
                <DropdownMenuRadioItem value="2">
                  2 per row
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="3">
                  3 per row
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="4">
                  4 per row
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>
          {/* DropdownMenu for filtering by tags */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                <ListOrderedIcon className="w-4 h-4" />
                Filter by {filterTag || "tags"}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-[200px] bg-white dark:text-foreground"
              align="end"
            >
              <DropdownMenuRadioGroup
                value={filterTag}
                onValueChange={(value: string) => setFilterTag(value)}
              >
                {classNames.map((tag) => (
                  <DropdownMenuRadioItem key={tag} value={tag}>
                    {tag}
                  </DropdownMenuRadioItem>
                ))}
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      {currentImages.length > 0 ? (
        <div
          className={`grid gap-4 md:gap-6 ${
            imagesPerRow === 2
              ? "grid-cols-1 sm:grid-cols-2"
              : imagesPerRow === 3
              ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3"
              : "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
          }`}
        >
          {currentImages.map((image, index) => (
            <div
              key={image.id}
              onClick={() => openImageViewer(index)}
              className="cursor-pointer"
            >
              <ImageCard image={image} />
            </div>
          ))}
        </div>
      ) : (
        <p className="text-center text-lg mt-6">No images found</p>
      )}
      <div className="flex justify-center mt-6">
        {/* Pagination */}
        <Pagination>
          <PaginationPrevious
            onClick={() => handlePageChange(currentPage - 1)}
          />
          <PaginationContent>
            {getPageNumbers().map((page, index) =>
              page === "..." ? (
                <PaginationItem key={index}>
                  <PaginationLink>{page}</PaginationLink>
                </PaginationItem>
              ) : (
                <PaginationItem key={index}>
                  <PaginationLink
                    isActive={page === currentPage}
                    onClick={() => handlePageChange(Number(page))}
                  >
                    {page}
                  </PaginationLink>
                </PaginationItem>
              )
            )}
          </PaginationContent>
          <PaginationNext onClick={() => handlePageChange(currentPage + 1)} />
        </Pagination>
      </div>
      {/* ImageViewer Modal */}
      {showImageViewer && (
        <ImageView
          images={images.map((img) => img.src)}
          initialIndex={selectedImageIndex}
          onClose={closeImageViewer}
        />
      )}
    </div>
  );
}
