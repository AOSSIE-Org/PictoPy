import React, { useMemo, useRef, useState, useEffect } from "react";
import CollagePreview from "./CollagePreview";
import { LayoutType, getLayout } from "./layouts";
import { Image as PictoImage } from "@/types/Media";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function CollageMaker({
  images,
  initialLayout = "grid2x2",
  maxFiles = 5,
}: {
  images?: PictoImage[];
  initialLayout?: LayoutType;
  maxFiles?: number;
}) {
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const [layout, setLayout] = useState<LayoutType>(initialLayout);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  const previewRef = useRef<HTMLDivElement>(null);

  // Normalize images from props
  const normalizedFromProps = useMemo(() => {
    if (!images?.length) return [];
    return images
      .map((img: any) =>
        img?.thumbnailPath
          ? `${API_BASE_URL}/uploads/${img.thumbnailPath.split(/[\\/]/).pop()}`
          : ""
      )
      .filter(Boolean);
  }, [images]);

  const finalImages = uploadedImages.length > 0 ? uploadedImages : normalizedFromProps;

  // Handle file uploads using persistent Blob URLs
  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    if (files.length > maxFiles) {
      alert(`Select up to ${maxFiles} images`);
      return;
    }

    const blobUrls = files.map((file) => URL.createObjectURL(file));
    setUploadedImages(blobUrls);
    setError(null);
  };

  // Cleanup Blob URLs to avoid memory leaks
  useEffect(() => {
    return () => {
      uploadedImages.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [uploadedImages]);

  // Download canvas logic
  const downloadImage = async (format: "image/png" | "image/jpeg") => {
    if (!previewRef.current) return;

    const rect = previewRef.current.getBoundingClientRect();
    const canvas = document.createElement("canvas");
    canvas.width = rect.width;
    canvas.height = rect.height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const config = getLayout(layout);

    const imgs = await Promise.all(
      finalImages.slice(0, config.maxImages).map(
        (src) =>
          new Promise<HTMLImageElement>((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => resolve(img);
            img.onerror = () => reject(`Failed to load image: ${src}`);
            img.src = src;
          })
      )
    );

    config.placements.forEach((p, i) => {
      if (!imgs[i]) return;
      const x = (p.colStart - 1) * (canvas.width / config.cols);
      const y = (p.rowStart - 1) * (canvas.height / config.rows);
      const w = (p.colEnd - p.colStart) * (canvas.width / config.cols);
      const h = (p.rowEnd - p.rowStart) * (canvas.height / config.rows);
      ctx.drawImage(imgs[i], x, y, w, h);
    });

    const a = document.createElement("a");
    a.href = canvas.toDataURL(format);
    a.download = format === "image/png" ? "collage.png" : "collage.jpg";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-300 dark:border-gray-700">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        📸 Instant Collage Generator
      </h2>

      <div className="flex gap-4 items-center">
        <select
          value={layout}
          onChange={(e) => setLayout(e.target.value as LayoutType)}
          className="p-2 rounded border bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-200 border-gray-400 dark:border-gray-600"
        >
          <option value="grid2x2">Grid 2×2</option>
          <option value="sideBySide">Side by Side</option>
          <option value="onePlusThreeSplit">1 + 3 Split</option>
        </select>

        <span className="text-sm px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
          {finalImages.length} image(s)
        </span>

        <label
          htmlFor="file-upload"
          className="ml-auto px-4 py-2 rounded border cursor-pointer bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          Choose Images
          <input
            id="file-upload"
            type="file"
            multiple
            accept="image/*"
            className="hidden"
            onChange={handleFiles}
          />
        </label>

        {/* Clickable Download Dropdown */}
        {finalImages.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowDropdown((prev) => !prev)}
              className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              Download ▼
            </button>

            {showDropdown && (
              <div className="absolute right-0 mt-2 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded shadow-lg z-10 min-w-full">
                <button
                  onClick={() => {
                    downloadImage("image/png");
                    setShowDropdown(false);
                  }}
                  className="block px-4 py-2 w-full text-left hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  PNG
                </button>
                <button
                  onClick={() => {
                    downloadImage("image/jpeg");
                    setShowDropdown(false);
                  }}
                  className="block px-4 py-2 w-full text-left hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  JPG
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}

      {/* Preview stays intact */}
      <div ref={previewRef}>
        <CollagePreview images={finalImages} layout={layout} />
      </div>
    </div>
  );
}

export default CollageMaker;
