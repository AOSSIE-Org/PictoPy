import React, { useState, useCallback, useEffect } from 'react';
import { Upload, Download, Trash2, RefreshCw } from 'lucide-react';
import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';

// Improved environment checker utility
const isTauriApp = () => {
  const isTauri =
    typeof window !== 'undefined' && window.__TAURI__ !== undefined;
  console.log('Environment check - Tauri available:', isTauri);
  return isTauri;
};

// Define the CompressedImage interface
interface CompressedImage {
  id: string;
  originalFile: File;
  originalSize: number;
  compressedSize: number;
  compressedBlob: Blob;
  previewUrl: string;
}

// Define the notification interface
interface Notification {
  type: 'success' | 'error';
  message: string;
  id: string;
}

const ImageCompressor: React.FC = () => {
  const [compressedImages, setCompressedImages] = useState<CompressedImage[]>(
    [],
  );
  const [isCompressing, setIsCompressing] = useState<boolean>(false);
  const [downloadingImages, setDownloadingImages] = useState<string[]>([]);
  const [compressionLevel, setCompressionLevel] = useState<number>(0.7);
  const [maxWidth, setMaxWidth] = useState<number>(1920);
  const [maxHeight, setMaxHeight] = useState<number>(1080);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isTauriEnvironment, setIsTauriEnvironment] = useState<boolean>(false);

  // Check if we're running in a Tauri environment or a browser
  useEffect(() => {
    try {
      console.log('Running environment check...');
      const isInTauri = isTauriApp();
      console.log('Setting environment state to:', isInTauri);
      setIsTauriEnvironment(isInTauri);

      // Check for Tauri plugins availability
      if (isInTauri) {
        console.log('Tauri import check - Dialog plugin:', typeof save);
        console.log('Tauri import check - FS plugin:', typeof writeFile);
        console.log(
          'Running in Tauri environment. Will use native file dialog.',
        );
      } else {
        console.log(
          'Running in browser environment. Will use browser download API as fallback.',
        );
      }
    } catch (error) {
      console.error('Error during environment detection:', error);
      setIsTauriEnvironment(false);
    }
  }, []);

  // Function to add a notification
  const addNotification = (type: 'success' | 'error', message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setNotifications((prev) => [...prev, { type, message, id }]);

    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 5000);
  };

  /**
   * Compresses an image file.
   * @param file - The image file to compress.
   * @returns A promise that resolves to the compressed image object.
   */
  const compressImage = useCallback(
    async (file: File): Promise<CompressedImage> => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (event) => {
          const img = new Image();
          img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            if (!ctx) {
              reject('Failed to get canvas context');
              return;
            }

            let width = img.width;
            let height = img.height;

            // Adjust dimensions to fit within maxWidth and maxHeight
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

            // Convert canvas to Blob
            canvas.toBlob(
              (blob) => {
                if (blob) {
                  const compressedImage: CompressedImage = {
                    id: Math.random().toString(36).substring(2, 9),
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

  /**
   * Handles file upload and compresses the selected images.
   * @param event - The file input change event.
   */
  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setIsCompressing(true);
      try {
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
      } catch (error) {
        console.error('Error compressing images:', error);
      } finally {
        setIsCompressing(false);
      }
    }
  };

  /**
   * Handles downloading in browser environment using the browser's download API.
   * @param image - The compressed image to download.
   */
  const handleBrowserDownload = (image: CompressedImage) => {
    try {
      // Check if the browser supports the download attribute
      const isDownloadSupported = 'download' in document.createElement('a');

      if (!isDownloadSupported) {
        throw new Error('Your browser does not support the download feature');
      }

      // Create a download link
      const url = URL.createObjectURL(image.compressedBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compressed_${image.originalFile.name}`;

      // Append to the document and trigger click
      document.body.appendChild(a);
      a.click();

      // Clean up
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);

      // Show a success notification
      addNotification('success', 'Download Successful');
    } catch (error) {
      console.error('Error downloading file in browser:', error);
      // Show an error notification with more specific message
      let errorMessage = 'Failed to download image';

      if (error instanceof Error) {
        errorMessage = `${errorMessage}: ${error.message}`;
      }

      addNotification('error', errorMessage);
    }
  };

  /**
   * Handles downloading a compressed image.
   * @param image - The compressed image to download.
   */
  const handleDownload = async (image: CompressedImage) => {
    console.log('Download initiated for image:', image.originalFile.name);
    try {
      // Set downloading state
      setDownloadingImages((prev) => [...prev, image.id]);
      console.log('Download state set, checking environment...');

      // Choose download method based on environment
      if (isTauriEnvironment) {
        console.log('Using Tauri native dialog for download');
        try {
          // Tauri desktop environment - use native save dialog
          // Show the save dialog to let the user choose where to save the file
          const defaultPath = `compressed_${image.originalFile.name}`;
          console.log(
            'Calling Tauri save dialog with defaultPath:',
            defaultPath,
          );

          const filePath = await save({
            defaultPath,
            title: 'Save Compressed Image',
            filters: [
              {
                name: 'Images',
                extensions: ['jpg', 'jpeg', 'png'],
              },
            ],
          });

          console.log(
            'Save dialog result:',
            filePath ? `Path selected: ${filePath}` : 'Dialog canceled',
          );

          // If user canceled the dialog
          if (!filePath) {
            console.log('User canceled the save dialog');
            setDownloadingImages((prev) =>
              prev.filter((id) => id !== image.id),
            );
            return;
          }

          // Convert the Blob to an ArrayBuffer
          console.log('Converting blob to ArrayBuffer...');
          const arrayBuffer = await image.compressedBlob.arrayBuffer();
          // Convert ArrayBuffer to Uint8Array which Tauri's writeFile expects
          const uint8Array = new Uint8Array(arrayBuffer);

          // Write the file to the selected location
          console.log('Writing file to:', filePath);
          await writeFile(filePath, uint8Array);
          console.log('File successfully written');

          // Show a success notification
          addNotification('success', 'Download Successful');
        } catch (tauriError) {
          console.error('Tauri download error details:', tauriError);
          console.warn(
            'Tauri save dialog failed, falling back to browser download',
          );
          // If Tauri APIs fail for some reason, fall back to browser download
          handleBrowserDownload(image);
        }
      } else {
        console.log('Using browser download API');
        // Browser environment - use browser's download API
        handleBrowserDownload(image);
      }
    } catch (error) {
      console.error('Error saving file:', error);
      // Show an error notification
      addNotification('error', `Failed to save image: ${error}`);
    } finally {
      // Clear downloading state
      console.log('Clearing download state');
      setDownloadingImages((prev) => prev.filter((id) => id !== image.id));
    }
  };

  /**
   * Handles removing a compressed image from the list.
   * @param id - The ID of the compressed image to remove.
   */
  const handleRemove = (id: string) => {
    setCompressedImages((prev) => prev.filter((img) => img.id !== id));
  };

  /**
   * Handles recompressing an image.
   * @param image - The compressed image to recompress.
   */
  const handleRecompress = async (image: CompressedImage) => {
    setIsCompressing(true);
    try {
      const recompressedImage = await compressImage(image.originalFile);
      setCompressedImages((prev) =>
        prev.map((img) => (img.id === image.id ? recompressedImage : img)),
      );
    } catch (error) {
      console.error('Error recompressing image:', error);
    } finally {
      setIsCompressing(false);
    }
  };

  return (
    <div className="rounded-xl relative bg-white/80 p-6 shadow-lg backdrop-blur-sm dark:bg-gray-800/80">
      {/* Notifications */}
      <div className="absolute bottom-4 right-4 z-50 w-72 space-y-2">
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className={`translate-y-0 transform rounded-lg p-3 text-white opacity-100 shadow-md transition-all duration-300 ${
              notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'
            }`}
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">{notification.message}</p>
              <button
                onClick={() =>
                  setNotifications((prev) =>
                    prev.filter((n) => n.id !== notification.id),
                  )
                }
                className="ml-2 text-white/70 hover:text-white"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>

      <h3 className="mb-6 bg-gradient-to-r from-blue-500 to-indigo-600 bg-clip-text text-xl font-bold text-transparent">
        Image Compressor
      </h3>

      <div className="mb-6 space-y-4">
        {/* Compression Level Slider */}
        <div className="rounded-lg bg-white/50 p-4 shadow-sm dark:bg-gray-700/50">
          <label
            htmlFor="compression-level"
            className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Compression Level:{' '}
            <span className="font-semibold text-blue-600">
              {compressionLevel}
            </span>
          </label>
          <input
            type="range"
            id="compression-level"
            min="0.1"
            max="1"
            step="0.1"
            value={compressionLevel}
            onChange={(e) => setCompressionLevel(parseFloat(e.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-500 dark:bg-gray-600"
          />
        </div>

        {/* Max Width Slider */}
        <div className="rounded-lg bg-white/50 p-4 shadow-sm dark:bg-gray-700/50">
          <label
            htmlFor="max-width"
            className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Max Width:{' '}
            <span className="font-semibold text-blue-600">{maxWidth}px</span>
          </label>
          <input
            type="range"
            id="max-width"
            min="100"
            max="3840"
            step="100"
            value={maxWidth}
            onChange={(e) => setMaxWidth(parseInt(e.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-500 dark:bg-gray-600"
          />
        </div>

        {/* Max Height Slider */}
        <div className="rounded-lg bg-white/50 p-4 shadow-sm dark:bg-gray-700/50">
          <label
            htmlFor="max-height"
            className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Max Height:{' '}
            <span className="font-semibold text-blue-600">{maxHeight}px</span>
          </label>
          <input
            type="range"
            id="max-height"
            min="100"
            max="2160"
            step="100"
            value={maxHeight}
            onChange={(e) => setMaxHeight(parseInt(e.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-500 dark:bg-gray-600"
          />
        </div>
      </div>

      {/* File Upload Button */}
      <div className="mb-6">
        <label
          htmlFor="file-upload"
          className="inline-flex cursor-pointer items-center rounded-lg bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-3 text-white shadow-lg transition-all duration-300 hover:scale-[1.02] hover:shadow-xl active:scale-[0.98]"
        >
          <Upload className="mr-2" size={18} />
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

      {/* Compressing Indicator */}
      {isCompressing && (
        <div className="mb-6 flex items-center justify-center rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
          <div className="rounded-full mr-3 h-4 w-4 animate-spin border-2 border-blue-600 border-t-transparent"></div>
          <p className="font-medium text-blue-600 dark:text-blue-400">
            Compressing images...
          </p>
        </div>
      )}

      {/* Compressed Images List */}
      <ul className="space-y-6">
        {compressedImages.map((image) => (
          <li
            key={image.id}
            className="rounded-xl bg-gradient-to-r from-gray-50 to-gray-100 p-5 shadow-md transition-all duration-300 hover:shadow-lg dark:from-gray-800/70 dark:to-gray-900/70"
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="mr-2 flex-grow truncate text-sm font-medium">
                {image.originalFile.name}
              </span>
              <div className="flex space-x-3">
                {/* Download Button */}
                <button
                  onClick={() => handleDownload(image)}
                  disabled={downloadingImages.includes(image.id)}
                  className={`rounded-full p-2 transition-all duration-300 ${
                    downloadingImages.includes(image.id)
                      ? 'cursor-not-allowed bg-blue-100 text-blue-400 dark:bg-blue-900/50 dark:text-blue-300'
                      : 'bg-blue-50 text-blue-500 hover:bg-blue-100 hover:text-blue-700 dark:bg-blue-900/20 dark:hover:bg-blue-900/30'
                  }`}
                  title="Save compressed image"
                >
                  {downloadingImages.includes(image.id) ? (
                    <div className="h-4.5 w-4.5 rounded-full animate-spin border-2 border-blue-500 border-t-transparent" />
                  ) : (
                    <Download size={18} />
                  )}
                </button>

                {/* Recompress Button */}
                <button
                  onClick={() => handleRecompress(image)}
                  className="rounded-full bg-green-50 p-2 text-green-500 transition-all duration-300 hover:bg-green-100 hover:text-green-700 dark:bg-green-900/20 dark:hover:bg-green-900/30"
                  title="Recompress image"
                >
                  <RefreshCw size={18} />
                </button>

                {/* Remove Button */}
                <button
                  onClick={() => handleRemove(image.id)}
                  className="rounded-full bg-red-50 p-2 text-red-500 transition-all duration-300 hover:bg-red-100 hover:text-red-700 dark:bg-red-900/20 dark:hover:bg-red-900/30"
                  title="Remove image"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>

            {/* Image Preview and Details */}
            <div className="flex items-center space-x-6">
              <div className="h-24 w-24 overflow-hidden rounded-lg border border-gray-200 shadow-md transition-transform duration-300 hover:scale-105 dark:border-gray-700">
                <img
                  src={image.previewUrl}
                  alt="Preview"
                  className="h-full w-full object-cover"
                />
              </div>
              <div className="flex-1 rounded-lg bg-white/50 p-3 shadow-sm dark:bg-gray-800/50">
                <div className="grid grid-cols-2 gap-2">
                  <p className="text-sm">
                    <span className="text-gray-500 dark:text-gray-400">
                      Original:
                    </span>
                    <span className="ml-2 font-medium">
                      {(image.originalSize / 1024).toFixed(2)} KB
                    </span>
                  </p>
                  <p className="text-sm">
                    <span className="text-gray-500 dark:text-gray-400">
                      Compressed:
                    </span>
                    <span className="ml-2 font-medium">
                      {(image.compressedSize / 1024).toFixed(2)} KB
                    </span>
                  </p>
                </div>
                <div className="mt-1 rounded-md bg-green-50 p-2 dark:bg-green-900/20">
                  <p className="text-sm font-medium text-green-600 dark:text-green-400">
                    Saved{' '}
                    {(
                      (image.originalSize - image.compressedSize) /
                      1024
                    ).toFixed(2)}{' '}
                    KB
                    <span className="rounded-full ml-1 inline-block bg-green-100 px-2 py-0.5 text-xs text-green-800 dark:bg-green-800/40 dark:text-green-300">
                      {(
                        ((image.originalSize - image.compressedSize) /
                          image.originalSize) *
                        100
                      ).toFixed(1)}
                      %
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ImageCompressor;
