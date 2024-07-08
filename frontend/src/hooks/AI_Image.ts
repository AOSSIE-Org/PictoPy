import { useState, useEffect } from "react";
import { convertFileSrc } from "@tauri-apps/api/core";

interface Image {
  id: string;
  date: string;
  title: string;
  popularity: number;
  src: string;
  tags: string[];
}

const initialData = {
  "E:/work/gsoc/New folder/PictoPy/images/001.jpg": "broccoli, bowl",
  "/home/bassam/Documents/os/PictoPy/images/000000000025.jpg": "giraffe",
  "/home/bassam/Documents/os/PictoPy/images/000000000030.jpg":
    "vase, potted plant",
  "/home/bassam/Documents/os/PictoPy/images/000000000034.jpg": "zebra",
  "/home/bassam/Documents/os/PictoPy/images/001.jpg": "person",
  "/home/bassam/Documents/os/PictoPy/images/001.png": "person, car",
  "/home/bassam/Documents/os/PictoPy/images/002.jpg": "person, tie",
  "/home/bassam/Documents/os/PictoPy/images/004.png":
    "bowl, cup, dining table, bottle, fork, spoon, knife, wine glass",
  "/home/bassam/Documents/os/PictoPy/images/cat.png": "cat",
  "/home/bassam/Documents/os/PictoPy/images/zidane.jpg": "person, tie",
};

const useAIImage = (folderPath: string) => {
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulating fetching data, replace with actual API call if needed
        const allImageObjects = initialData;

        const parsedAndSortedImages = parseAndSortImageData(allImageObjects);
        setImages(parsedAndSortedImages);
      } catch (error) {
        console.error("Error fetching images:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [folderPath]);

  const parseAndSortImageData = (data: any): Image[] => {
    const parsedImages: Image[] = Object.entries(data).map(
      ([src, tags], index) => {
        const srcc = convertFileSrc(src);
        return {
          id: String(index),
          date: new Date().toISOString(),
          title: src.substring(src.lastIndexOf("/") + 1),
          popularity: tags.split(", ").length,
          src: srcc,
          tags: tags.split(", "),
        };
      }
    );

    parsedImages.sort((a, b) => b.popularity - a.popularity);

    return parsedImages;
  };

  return { images, loading };
};

export default useAIImage;
