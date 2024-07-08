import React from "react";
import { useImages } from "../../hooks/useImages";

import ImageGallery from "@/components/Photos/ImageGallery";

const Photos: React.FC = () => {
  const localPath = localStorage.getItem("folderPath") || "";
  const { images, loading } = useImages(localPath);

  if (loading) {
    return <div>Loading images...</div>;
  }

  return (
    <div>
      <ImageGallery images={images} title={localPath} />
    </div>
  );
};

export default Photos;
