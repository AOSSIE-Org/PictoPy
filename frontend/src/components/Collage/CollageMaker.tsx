import React, { useMemo, useState } from "react";
import { Image as PictoImage } from "@/types/Media";
import CollagePreview from "./CollagePreview";
import { LayoutType } from "./layouts";

export interface CollageMakerProps {
  images?: PictoImage[];
  initialLayout?: LayoutType;
  maxFiles?: number;
}

export function CollageMaker({
  images,
  initialLayout = "grid2x2", 
  maxFiles = 5,
}: CollageMakerProps) {
  const [uploaded, setUploaded] = useState<string[]>([]);
  const [layout, setLayout] = useState<LayoutType>(initialLayout);

  const getThumbnailUrl = (img: any) => {
    if (!img?.thumbnailPath) return "";
    const fileName = img.thumbnailPath.split("\\").pop(); 
    return `http://localhost:8000/uploads/${fileName}`;
  };

  const normalizedFromProps = useMemo(() => {
    if (!images || images.length === 0) return [];
    return images.map((img: any) => getThumbnailUrl(img)).filter(Boolean);
  }, [images]);

  const normalizedImages =
    uploaded.length > 0 ? uploaded : normalizedFromProps;

  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    if (files.length > maxFiles) {
      alert(`Select up to ${maxFiles} images`);
      return;
    }

    Promise.all(
      files.map(
        (file) =>
          new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.readAsDataURL(file);
          })
      )
    ).then(setUploaded);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 bg-gray-50 rounded-xl shadow-2xl shadow-blue-100"> 
      <h2 className="text-2xl font-bold text-gray-800 border-b pb-3">
        📸 Instant Collage Generator
      </h2>

      {/* Action Row containing Layout, Count, and Choose File button */}
      <div className="flex gap-4 items-center">
        
        {/* Layout Selector */}
        <label htmlFor="layout-select" className="text-gray-700 font-medium">
          Select Layout:
        </label>
        <select
          id="layout-select"
          value={layout}
          onChange={(e) => setLayout(e.target.value as LayoutType)}
          // Hand icon added here
          className="p-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-blue-400 transition duration-150 bg-white cursor-pointer"
        >
          <option value="grid2x2">Grid 2×2</option> 
          <option value="sideBySide">Side by Side</option>
          <option value="onePlusThreeSplit">1 + 3 Split</option>
        </select>

        {/* Image Count */}
        <span className="text-sm ml-auto text-blue-600 font-semibold bg-blue-50 px-3 py-1 rounded-full">
          {normalizedImages.length} image(s)
        </span>
        
        {/* Choose File Button: Hand icon and reliable click pattern */}
        <label 
          htmlFor="file-upload" 
          // Hand icon added here for reliable click/UX
          className="px-3 py-2 text-sm text-gray-700 font-medium border border-gray-300 rounded-lg bg-white hover:bg-gray-100 transition duration-150 cursor-pointer shadow-sm inline-flex items-center justify-center whitespace-nowrap"
        >
          Choose File(s)
          <input
            id="file-upload"
            type="file"
            accept="image/*"
            multiple
            onChange={handleFiles}
            className="hidden" 
          />
        </label>
      </div>

      <CollagePreview images={normalizedImages} layout={layout} />
    </div>
  );
}

export default CollageMaker;