import React, { useState, useCallback } from 'react';
import { Upload, Download, Trash2, RefreshCw } from 'lucide-react';

interface CompressedImage {
  id: string;
  originalFile: File;
  originalSize: number;
  compressedSize: number;
  compressedBlob: Blob;
  previewUrl: string;
}

const ImageCompressor: React.FC = () => {
  const [compressedImages, setCompressedImages] = useState<CompressedImage[]>(
    [],
  );
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionLevel, setCompressionLevel] = useState(0.7);
  const [maxWidth, setMaxWidth] = useState(1920);
  const [maxHeight, setMaxHeight] = useState(1080);

  const compressImage = useCallback(
    async (file: File): Promise<CompressedImage> => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (event) => {
          const img = new Image();
          img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d')!;

            let width = img.width;
            let height = img.height;

            if (width > maxWidth) {
              height *= maxWidth / width;
              width = maxWidth;
            }

            if (height > maxHeight) {
              width *= maxHeight / height;
              height = maxHeight;
            }

            canvas.width = width;
            canvas.height = height;

            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob(
              (blob) => {
                if (blob) {
                  const compressedImage: CompressedImage = {
                    id: Math.random().toString(36).substr(2, 9),
                    originalFile: file,
                    originalSize: file.size,
                    compressedSize: blob.size,
                    compressedBlob: blob,
                    previewUrl: URL.createObjectURL(blob),
                  };
                  resolve(compressedImage);
                } else {
                  reject('Failed to compress image');
                }
              },
              'image/jpeg',
              compressionLevel,
            );
          };
          img.onerror = () => reject('Image load failed');
          img.src = event.target?.result as string;
        };
        reader.onerror = () => reject('File reading failed');
        reader.readAsDataURL(file);
      });
    },
    [compressionLevel, maxWidth, maxHeight],
  );

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const files = event.target.files;
    if (files) {
      setIsCompressing(true);
      const compressedFiles = await Promise.all(
        Array.from(files).map((file) =>
          compressImage(file).catch((err) => {
            console.error('Compression failed:', err);
            return null;
          }),
        ),
      );
      setCompressedImages((prev) => [
        ...prev,
        ...compressedFiles.filter((file) => file !== null),
      ]);
      setIsCompressing(false);
    }
  };

  const handleDownload = (image: CompressedImage) => {
    const url = URL.createObjectURL(image.compressedBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compressed_${image.originalFile.name}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleRemove = (id: string) => {
    setCompressedImages((prev) => prev.filter((img) => img.id !== id));
  };

  const handleRecompress = async (image: CompressedImage) => {
    setIsCompressing(true);
    const recompressedImage = await compressImage(image.originalFile);
    setCompressedImages((prev) =>
      prev.map((img) => (img.id === image.id ? recompressedImage : img)),
    );
    setIsCompressing(false);
  };

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="mb-4 text-lg font-semibold">Image Compressor</h3>
      <div className="mb-4 space-y-2">
        <div>
          <label
            htmlFor="compression-level"
            className="block text-sm font-medium text-gray-700"
          >
            Compression Level: {compressionLevel}
          </label>
          <input
            type="range"
            id="compression-level"
            min="0.1"
            max="1"
            step="0.1"
            value={compressionLevel}
            onChange={(e) => setCompressionLevel(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
        <div>
          <label
            htmlFor="max-width"
            className="block text-sm font-medium text-gray-700"
          >
            Max Width: {maxWidth}px
          </label>
          <input
            type="range"
            id="max-width"
            min="100"
            max="3840"
            step="100"
            value={maxWidth}
            onChange={(e) => setMaxWidth(parseInt(e.target.value))}
            className="w-full"
          />
        </div>
        <div>
          <label
            htmlFor="max-height"
            className="block text-sm font-medium text-gray-700"
          >
            Max Height: {maxHeight}px
          </label>
          <input
            type="range"
            id="max-height"
            min="100"
            max="2160"
            step="100"
            value={maxHeight}
            onChange={(e) => setMaxHeight(parseInt(e.target.value))}
            className="w-full"
          />
        </div>
      </div>
      <div className="mb-4">
        <label
          htmlFor="file-upload"
          className="inline-flex cursor-pointer items-center rounded bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600"
        >
          <Upload className="mr-2" size={16} />
          Upload Images
        </label>
        <input
          id="file-upload"
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>
      {isCompressing && <p className="text-gray-600">Compressing images...</p>}
      <ul className="space-y-4">
        {compressedImages.map((image) => (
          <li key={image.id} className="rounded-lg bg-gray-100 p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="mr-2 flex-grow truncate text-sm font-medium">
                {image.originalFile.name}
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleDownload(image)}
                  className="text-blue-500 transition-colors hover:text-blue-700"
                  title="Download compressed image"
                >
                  <Download size={20} />
                </button>
                <button
                  onClick={() => handleRecompress(image)}
                  className="text-green-500 transition-colors hover:text-green-700"
                  title="Recompress image"
                >
                  <RefreshCw size={20} />
                </button>
                <button
                  onClick={() => handleRemove(image.id)}
                  className="text-red-500 transition-colors hover:text-red-700"
                  title="Remove image"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <img
                src={image.previewUrl}
                alt="Preview"
                className="h-20 w-20 rounded object-cover"
              />
              <div>
                <p className="text-sm">
                  Original: {(image.originalSize / 1024).toFixed(2)} KB
                </p>
                <p className="text-sm">
                  Compressed: {(image.compressedSize / 1024).toFixed(2)} KB
                </p>
                <p className="text-sm">
                  Saved:{' '}
                  {((image.originalSize - image.compressedSize) / 1024).toFixed(
                    2,
                  )}{' '}
                  KB (
                  {(
                    ((image.originalSize - image.compressedSize) /
                      image.originalSize) *
                    100
                  ).toFixed(2)}
                  %)
                </p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ImageCompressor;
