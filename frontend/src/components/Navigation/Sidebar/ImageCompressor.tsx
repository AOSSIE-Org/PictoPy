import React, { useState, useCallback } from 'react';
import { Upload, Download, Trash2, RefreshCw, Settings, X } from 'lucide-react';

interface CompressedImage {
  id: string;
  originalFile: File;
  originalSize: number;
  compressedSize: number;
  compressedBlob: Blob;
  previewUrl: string;
  outputFormat: string;
}

const ImageProcessor: React.FC = () => {
  const [compressedImages, setCompressedImages] = useState<CompressedImage[]>(
    [],
  );
  const [isCompressing, setIsCompressing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [compressionLevel, setCompressionLevel] = useState(0.7);
  const [maxWidth, setMaxWidth] = useState(1920);
  const [maxHeight, setMaxHeight] = useState(1080);
  const [outputFormat, setOutputFormat] = useState('image/jpeg');

  const formatOptions = [
    { value: 'image/jpeg', label: 'JPEG' },
    { value: 'image/png', label: 'PNG' },
    { value: 'image/webp', label: 'WebP' },
  ];

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

            if (outputFormat === 'image/jpeg') {
              ctx.fillStyle = '#FFFFFF';
              ctx.fillRect(0, 0, width, height);
            }

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
                    outputFormat: outputFormat,
                  };
                  resolve(compressedImage);
                } else {
                  reject('Failed to compress image');
                }
              },
              outputFormat,
              outputFormat === 'image/png' ? undefined : compressionLevel,
            );
          };
          img.onerror = () => reject('Image load failed');
          img.src = event.target?.result as string;
        };
        reader.onerror = () => reject('File reading failed');
        reader.readAsDataURL(file);
      });
    },
    [compressionLevel, maxWidth, maxHeight, outputFormat],
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
        ...compressedFiles.filter(
          (file): file is CompressedImage => file !== null,
        ),
      ]);
      setIsCompressing(false);
    }
  };

  const handleDownload = (image: CompressedImage) => {
    const url = URL.createObjectURL(image.compressedBlob);
    const a = document.createElement('a');
    a.href = url;
    const extension = image.outputFormat.split('/')[1];
    a.download = `compressed_${image.originalFile.name.split('.')[0]}.${extension}`;
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
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-8 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 p-6 shadow-lg">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800">Image Processor</h2>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
          >
            <Settings size={18} />
            Settings
          </button>
        </div>

        {showSettings && (
          <div className="relative mb-6 rounded-lg bg-white p-6">
            <button
              onClick={() => setShowSettings(false)}
              className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
            >
              <X size={20} />
            </button>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Output Format
                </label>
                <select
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 p-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                >
                  {formatOptions.map((format) => (
                    <option key={format.value} value={format.value}>
                      {format.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Compression Level: {compressionLevel}
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={compressionLevel}
                  onChange={(e) =>
                    setCompressionLevel(parseFloat(e.target.value))
                  }
                  className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Max Width: {maxWidth}px
                </label>
                <input
                  type="range"
                  min="100"
                  max="3840"
                  step="100"
                  value={maxWidth}
                  onChange={(e) => setMaxWidth(parseInt(e.target.value))}
                  className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Max Height: {maxHeight}px
                </label>
                <input
                  type="range"
                  min="100"
                  max="2160"
                  step="100"
                  value={maxHeight}
                  onChange={(e) => setMaxHeight(parseInt(e.target.value))}
                  className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
                />
              </div>
            </div>
          </div>
        )}

        <div className="text-center">
          <label className="inline-block">
            <div className="flex cursor-pointer items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700">
              <Upload size={20} />
              Upload Images
            </div>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>

        {isCompressing && (
          <div className="mt-4 text-center">
            <div className="inline-flex items-center rounded-lg bg-blue-100 px-4 py-2 text-blue-700">
              <RefreshCw className="mr-2 animate-spin" size={18} />
              Processing images...
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6">
        {compressedImages.map((image) => (
          <div
            key={image.id}
            className="overflow-hidden rounded-xl bg-white shadow-md transition-shadow hover:shadow-lg"
          >
            <div className="p-4">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="truncate text-lg font-medium text-gray-800">
                  {image.originalFile.name}
                </h3>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleDownload(image)}
                    className="text-blue-600 transition-colors hover:text-blue-800"
                    title="Download processed image"
                  >
                    <Download size={20} />
                  </button>
                  <button
                    onClick={() => handleRecompress(image)}
                    className="text-green-600 transition-colors hover:text-green-800"
                    title="Reprocess image"
                  >
                    <RefreshCw size={20} />
                  </button>
                  <button
                    onClick={() => handleRemove(image.id)}
                    className="text-red-600 transition-colors hover:text-red-800"
                    title="Remove image"
                  >
                    <Trash2 size={20} />
                  </button>
                </div>
              </div>

              <div className="flex flex-col items-center gap-6 sm:flex-row">
                <div className="h-40 w-40 overflow-hidden rounded-lg bg-gray-100">
                  <img
                    src={image.previewUrl}
                    alt={`Preview of ${image.originalFile.name}`}
                    className="h-full w-full object-cover"
                  />
                </div>

                <div className="flex-grow">
                  <p className="mb-2 text-sm text-gray-600">
                    Original Size: {(image.originalSize / 1024).toFixed(2)} KB
                  </p>
                  <p className="mb-2 text-sm text-gray-600">
                    Compressed Size: {(image.compressedSize / 1024).toFixed(2)}{' '}
                    KB
                  </p>
                  <p className="text-sm text-gray-600">
                    Compression Ratio:{' '}
                    {(
                      (1 - image.compressedSize / image.originalSize) *
                      100
                    ).toFixed(2)}
                    %
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ImageProcessor;
