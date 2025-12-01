import React, { useMemo, useState } from "react";
import { Image as PictoImage } from "@/types/Media";
import CollagePreview from "./CollagePreview";
import { LayoutType } from "./layouts";

// FIX: Define API_BASE_URL using environment variable fallback (Addressing hardcoded URL)
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
  const [error, setError] = useState<string | null>(null);

  const getThumbnailUrl = (img: any) => {
    if (!img?.thumbnailPath) return "";

    // FIX: Use regex to handle both Windows (\) and Unix (/) path separators
    const fileName = img.thumbnailPath.split(/[\\/]/).pop();

    // FIX: Use API_BASE_URL instead of hardcoded URL
    return `${API_BASE_URL}/uploads/${fileName}`;
  };

  const normalizedFromProps = useMemo(() => {
    if (!images || images.length === 0) return [];
    return images.map((img: any) => getThumbnailUrl(img)).filter(Boolean);
  }, [images]);

  const normalizedImages =
    normalizedFromProps.length > 0 ? normalizedFromProps : uploaded;

  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    if (files.length > maxFiles) {
      alert(`Select up to ${maxFiles} images`);
      return;
    }

    setError(null); // Clear previous errors

    Promise.all(
      files.map(
        (file) =>
          new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            
            // FIX: Add onerror handler to prevent silent failure
            reader.onerror = () => reject(new Error(`Failed to read file: ${file.name}`)); 
            
            reader.readAsDataURL(file);
          })
      )
    )
      .then(setUploaded)
      .catch(err => {
          const errorMessage = err instanceof Error ? err.message : "An unknown error occurred while loading files.";
          setError(errorMessage);
          console.error("File loading error:", err);
          alert(errorMessage);
      });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 bg-gray-50 rounded-xl shadow-2xl shadow-blue-100"> 
      <h2 className="text-2xl font-bold text-gray-800 border-b pb-3">
        📸 Instant Collage Generator
      </h2>
      <div className="flex gap-4 items-center">
        <select
          id="layout-select"
          value={layout}
          onChange={(e) => setLayout(e.target.value as LayoutType)}
          className="p-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-blue-400 transition duration-150 bg-white cursor-pointer"
        >
          <option value="grid2x2">Grid 2×2</option> 
          <option value="sideBySide">Side by Side</option>
          <option value="onePlusThreeSplit">1 + 3 Split</option>
        </select>

        {/* Image Count (Next to Layout) */}
        <span className="text-sm text-blue-600 font-semibold bg-blue-50 px-3 py-1 rounded-full">
          {normalizedImages.length} image(s)
        </span>
        <label 
          htmlFor="file-upload" 
          // ml-auto pushes this element to the far right
          className="px-3 py-2 text-sm text-gray-700 font-medium border border-gray-300 rounded-lg bg-white hover:bg-gray-100 transition duration-150 cursor-pointer shadow-sm inline-flex items-center justify-center whitespace-nowrap ml-auto"
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
      
      {error && (
        <p className="text-red-600 text-sm p-2 border border-red-300 bg-red-50 rounded-lg">
          Error: {error}
        </p>
      )}

      <CollagePreview images={normalizedImages} layout={layout} />
    </div>
  );
}

export default CollageMaker;
