import React, { useState, useCallback, useEffect } from 'react';
import { Upload, Download, Trash2, RefreshCw } from 'lucide-react';
import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';

// Constants
const FORCE_MODE: boolean | null = null;
const DEBUG_MODE = true;
const debugLog = (...args: any[]) =>
  DEBUG_MODE && console.log('[DEBUG]', ...args);

// Interfaces
interface CompressedImage {
  id: string;
  originalFile: File;
  originalSize: number;
  compressedSize: number;
  compressedBlob: Blob;
  previewUrl: string;
}

interface Notification {
  type: 'success' | 'error';
  message: string;
  id: string;
}

// Custom Hooks
const useTauriCheck = () => {
  const [isTauri, setIsTauri] = useState(false);
  const [dialogAvailable, setDialogAvailable] = useState(false);

  useEffect(() => {
    const checkTauri = () => {
      const isTauriEnv =
        FORCE_MODE ??
        (typeof window !== 'undefined' &&
          ((window as any).__TAURI__ !== undefined ||
            window.location.port === '1420'));
      setIsTauri(!!isTauriEnv);
      setDialogAvailable(isTauriEnv && typeof save === 'function');
    };

    checkTauri();
  }, []);

  return { isTauri, dialogAvailable };
};

const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = (type: 'success' | 'error', message: string) => {
    const id = Math.random().toString(36).slice(2, 9);
    setNotifications((prev) => [...prev, { type, message, id }]);
    setTimeout(
      () => setNotifications((prev) => prev.filter((n) => n.id !== id)),
      5000,
    );
  };

  return { notifications, addNotification, setNotifications };
};

// Components
const SliderInput: React.FC<{
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}> = ({ label, value, min, max, step, onChange }) => (
  <div className="rounded-lg bg-white/50 p-4 shadow-sm dark:bg-gray-700/50">
    <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
      {label}: <span className="font-semibold text-blue-600">{value}</span>
    </label>
    <input
      type="range"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      min={min}
      max={max}
      step={step}
      className="h-2 w-full cursor-pointer rounded-lg bg-gray-200 accent-blue-500 dark:bg-gray-600"
    />
  </div>
);

const ImageCompressor: React.FC = () => {
  const { isTauri, dialogAvailable } = useTauriCheck();
  const { notifications, addNotification, setNotifications } =
    useNotifications();
  const [compressedImages, setCompressedImages] = useState<CompressedImage[]>(
    [],
  );
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionLevel, setCompressionLevel] = useState(0.7);
  const [maxWidth, setMaxWidth] = useState(1920);
  const [maxHeight, setMaxHeight] = useState(1080);

  const compressImage = useCallback(
    async (file: File): Promise<CompressedImage> => {
      const readFile = () =>
        new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.onerror = () => reject('File reading failed');
          reader.readAsDataURL(file);
        });

      const createImage = (src: string) =>
        new Promise<HTMLImageElement>((resolve, reject) => {
          const img = new Image();
          img.onload = () => resolve(img);
          img.onerror = () => reject('Image load failed');
          img.src = src;
        });

      const src = await readFile();
      const img = await createImage(src);

      let w = img.width;
      let h = img.height;

      if (w > maxWidth) {
        h = h * (maxWidth / w);
        w = maxWidth;
      }

      if (h > maxHeight) {
        w = w * (maxHeight / h);
        h = maxHeight;
      }

      const width = w;
      const height = h;

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      canvas.getContext('2d')?.drawImage(img, 0, 0, width, height);

      const blob = await new Promise<Blob>((resolve) =>
        canvas.toBlob((blob) => resolve(blob!), 'image/jpeg', compressionLevel),
      );

      return {
        id: Math.random().toString(36).slice(2, 9),
        originalFile: file,
        originalSize: file.size,
        compressedSize: blob.size,
        compressedBlob: blob,
        previewUrl: URL.createObjectURL(blob),
      };
    },
    [compressionLevel, maxWidth, maxHeight],
  );

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;

    setIsCompressing(true);
    try {
      const results = await Promise.all(
        Array.from(files).map((file) => compressImage(file).catch(() => null)),
      );
      setCompressedImages((prev) => [
        ...prev,
        ...(results.filter(Boolean) as CompressedImage[]),
      ]);
    } finally {
      setIsCompressing(false);
    }
  };

  const handleDownload = async (image: CompressedImage) => {
    debugLog('Starting download for image:', image.originalFile.name);

    const downloadBrowser = () => {
      debugLog('Using browser download API');
      const a = document.createElement('a');
      a.href = URL.createObjectURL(image.compressedBlob);
      a.download = `compressed_${image.originalFile.name}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
      addNotification('success', 'Download Successful');
    };

    try {
      if (isTauri && dialogAvailable) {
        debugLog('Using Tauri native save dialog');
        const fileName = `compressed_${image.originalFile.name}`;

        const path = await save({
          defaultPath: fileName,
          filters: [{ name: 'Images', extensions: ['jpg', 'jpeg', 'png'] }],
        });

        if (path) {
          debugLog('User selected path:', path);
          try {
            const arrayBuffer = await image.compressedBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);

            debugLog(`Writing file with size: ${uint8Array.length} bytes`);
            await writeFile(path, uint8Array);

            addNotification('success', 'Image saved successfully!');
            debugLog('File written successfully to', path);
          } catch (writeErr) {
            const error = writeErr as Error;
            console.error('Error writing file:', error);
            debugLog('Write error details:', error.message);
            debugLog('Falling back to browser download due to write error');

            addNotification('error', `Error saving file: ${error.message}`);
            downloadBrowser();
          }
        } else {
          debugLog('User cancelled save dialog');
        }
      } else {
        debugLog('Using browser download (Tauri unavailable)');
        downloadBrowser();
      }
    } catch (err) {
      const error = err as Error;
      console.error('Error during download:', error);
      debugLog('Falling back to browser download due to error:', error.message);

      let errorMessage = error.message || 'Unknown error';
      if (errorMessage === 'undefined' || errorMessage.includes('undefined')) {
        errorMessage = 'Native dialog plugin not responding correctly';
      }

      addNotification('error', `Error: ${errorMessage}`);
      downloadBrowser();
    }
  };

  return (
    <div className="rounded-xl relative bg-white/80 p-6 shadow-lg backdrop-blur-sm dark:bg-gray-800/80">
      <NotificationList
        notifications={notifications}
        setNotifications={setNotifications}
      />

      <h3 className="mb-6 bg-gradient-to-r from-blue-500 to-indigo-600 bg-clip-text text-xl font-bold text-transparent">
        Image Compressor
      </h3>

      <div className="mb-6 space-y-4">
        <SliderInput
          label="Compression Level"
          value={compressionLevel}
          min={0.1}
          max={1}
          step={0.1}
          onChange={setCompressionLevel}
        />
        <SliderInput
          label="Max Width"
          value={maxWidth}
          min={100}
          max={3840}
          step={100}
          onChange={setMaxWidth}
        />
        <SliderInput
          label="Max Height"
          value={maxHeight}
          min={100}
          max={2160}
          step={100}
          onChange={setMaxHeight}
        />
      </div>

      <FileUploadButton onChange={handleFileUpload} />

      {isCompressing && <CompressingIndicator />}

      <ul className="space-y-6">
        {compressedImages.map((image) => (
          <CompressedImageItem
            key={image.id}
            image={image}
            onDownload={() => handleDownload(image)}
            onRemove={() =>
              setCompressedImages((prev) =>
                prev.filter((i) => i.id !== image.id),
              )
            }
            onRecompress={async () => {
              setIsCompressing(true);
              try {
                const newImage = await compressImage(image.originalFile);
                setCompressedImages((prev) =>
                  prev.map((i) => (i.id === image.id ? newImage : i)),
                );
              } finally {
                setIsCompressing(false);
              }
            }}
          />
        ))}
      </ul>
    </div>
  );
};

// Helper Components
const NotificationList: React.FC<{
  notifications: Notification[];
  setNotifications: React.Dispatch<React.SetStateAction<Notification[]>>;
}> = ({ notifications, setNotifications }) => (
  <div className="absolute bottom-4 right-4 z-50 w-72 space-y-2">
    {notifications.map((n) => (
      <div
        key={n.id}
        className={`translate-y-0 transform rounded-lg p-3 text-white opacity-100 shadow-md transition-all duration-300 ${n.type === 'success' ? 'bg-green-500' : 'bg-red-500'}`}
      >
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">{n.message}</p>
          <button
            onClick={() =>
              setNotifications((prev) => prev.filter((not) => not.id !== n.id))
            }
            className="ml-2 text-white/70 hover:text-white"
          >
            ×
          </button>
        </div>
      </div>
    ))}
  </div>
);

const FileUploadButton: React.FC<{
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}> = ({ onChange }) => (
  <div className="mb-6">
    <label className="inline-flex cursor-pointer items-center rounded-lg bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-3 text-white shadow-lg transition-all duration-300 hover:scale-[1.02] hover:shadow-xl active:scale-[0.98]">
      <Upload className="mr-2" size={18} />
      Upload Images
      <input
        type="file"
        accept="image/*"
        multiple
        onChange={onChange}
        className="hidden"
      />
    </label>
  </div>
);

const CompressingIndicator: React.FC = () => (
  <div className="mb-6 flex items-center justify-center rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
    <div className="rounded-full mr-3 h-4 w-4 animate-spin border-2 border-blue-600 border-t-transparent" />
    <p className="font-medium text-blue-600 dark:text-blue-400">
      Compressing images...
    </p>
  </div>
);

const CompressedImageItem: React.FC<{
  image: CompressedImage;
  onDownload: () => void;
  onRemove: () => void;
  onRecompress: () => void;
}> = ({ image, onDownload, onRemove, onRecompress }) => (
  <li className="rounded-xl bg-gradient-to-r from-gray-50 to-gray-100 p-5 shadow-md transition-all duration-300 hover:shadow-lg dark:from-gray-800/70 dark:to-gray-900/70">
    <div className="mb-3 flex items-center justify-between">
      <span className="mr-2 flex-grow truncate text-sm font-medium">
        {image.originalFile.name}
      </span>
      <div className="flex space-x-3">
        <ActionButton
          onClick={onDownload}
          icon={<Download size={18} />}
          color="blue"
        />
        <ActionButton
          onClick={onRecompress}
          icon={<RefreshCw size={18} />}
          color="green"
        />
        <ActionButton
          onClick={onRemove}
          icon={<Trash2 size={18} />}
          color="red"
        />
      </div>
    </div>
    <div className="flex items-center space-x-6">
      <img
        src={image.previewUrl}
        alt="Preview"
        className="h-24 w-24 rounded-lg border border-gray-200 object-cover shadow-md dark:border-gray-700"
      />
      <ImageStats image={image} />
    </div>
  </li>
);

const ActionButton: React.FC<{
  onClick: () => void;
  icon: React.ReactNode;
  color: string;
}> = ({ onClick, icon, color }) => (
  <button
    onClick={onClick}
    className={`rounded-full p-2 transition-all duration-300 bg-${color}-50 text-${color}-500 hover:bg-${color}-100 hover:text-${color}-700 dark:bg-${color}-900/20 dark:hover:bg-${color}-900/30`}
  >
    {icon}
  </button>
);

const ImageStats: React.FC<{ image: CompressedImage }> = ({ image }) => {
  const savedKB = ((image.originalSize - image.compressedSize) / 1024).toFixed(
    2,
  );
  const savedPercent = (
    ((image.originalSize - image.compressedSize) / image.originalSize) *
    100
  ).toFixed(1);

  return (
    <div className="flex-1 rounded-lg bg-white/50 p-3 shadow-sm dark:bg-gray-800/50">
      <div className="grid grid-cols-2 gap-2">
        <Stat
          label="Original"
          value={`${(image.originalSize / 1024).toFixed(2)} KB`}
        />
        <Stat
          label="Compressed"
          value={`${(image.compressedSize / 1024).toFixed(2)} KB`}
        />
      </div>
      <div className="mt-1 rounded-md bg-green-50 p-2 dark:bg-green-900/20">
        <p className="text-sm font-medium text-green-600 dark:text-green-400">
          Saved {savedKB} KB{' '}
          <span className="rounded-full ml-1 inline-block bg-green-100 px-2 py-0.5 text-xs text-green-800 dark:bg-green-800/40 dark:text-green-300">
            {savedPercent}%
          </span>
        </p>
      </div>
    </div>
  );
};

const Stat: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <p className="text-sm">
    <span className="text-gray-500 dark:text-gray-400">{label}:</span>
    <span className="ml-2 font-medium">{value}</span>
  </p>
);

export default ImageCompressor;
