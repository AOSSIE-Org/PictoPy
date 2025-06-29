import React, { useState, useCallback } from 'react';
import Cropper, { Area } from 'react-easy-crop';

interface AvatarCropperProps {
  image: string;
  onCropComplete: (croppedImage: string) => void;
}

const AvatarCropper: React.FC<AvatarCropperProps> = ({
  image,
  onCropComplete,
}) => {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [croppedPreview, setCroppedPreview] = useState<string | null>(null);

  // Add type annotations for parameters
  const handleCropComplete = useCallback((_: Area, croppedAreaPixels: Area) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const createImage = (url: string): Promise<HTMLImageElement> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = url;
      img.onload = () => resolve(img);
      img.onerror = (error) => reject(error);
    });
  };

  // Add type annotation for crop parameter
  const getCroppedImg = async (imageSrc: string, crop: Area) => {
    const image = await createImage(imageSrc);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // Add null check for canvas context
    if (!ctx) {
      throw new Error('Canvas context not available');
    }

    canvas.width = crop.width;
    canvas.height = crop.height;

    ctx.drawImage(
      image,
      crop.x,
      crop.y,
      crop.width,
      crop.height,
      0,
      0,
      crop.width,
      crop.height,
    );

    return canvas.toDataURL('image/jpeg');
  };

  const handleCropImage = async () => {
    if (croppedAreaPixels) {
      try {
        const croppedImage = await getCroppedImg(image, croppedAreaPixels);
        onCropComplete(croppedImage);
        setCroppedPreview(croppedImage);
      } catch (error) {
        console.error('Cropping failed:', error);
      }
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 p-4">
      {/* Cropper Container with Stylish Border */}
      <div className="relative h-72 w-72 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 p-1 shadow-xl">
        <div className="h-full w-full overflow-hidden rounded-lg bg-gray-900">
          <Cropper
            image={image}
            crop={crop}
            zoom={zoom}
            aspect={1}
            onCropChange={setCrop}
            onZoomChange={setZoom}
            onCropComplete={handleCropComplete}
            classes={{
              containerClassName: 'rounded-lg',
              mediaClassName: 'rounded-lg',
            }}
          />
        </div>
      </div>

      {/* Zoom Control with Labels */}
      <div className="w-full max-w-xs space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
            Zoom
          </span>
          <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
            {zoom.toFixed(1)}x
          </span>
        </div>
        <div className="rounded-lg bg-white/50 p-2 shadow-sm dark:bg-gray-700/50">
          <input
            type="range"
            min={1}
            max={3}
            step={0.1}
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-blue-500 dark:bg-gray-600"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleCropImage}
          className="rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-2.5 text-white shadow-lg transition-all duration-300 hover:translate-y-[-1px] hover:shadow-xl focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none active:translate-y-[1px]"
        >
          Apply Crop
        </button>
      </div>

      {/* Cropped Preview */}
      {croppedPreview && (
        <div className="mt-2 w-full max-w-xs">
          <h3 className="mb-2 text-center text-sm font-semibold text-gray-600 dark:text-gray-300">
            Preview
          </h3>
          <div className="mx-auto h-32 w-32 overflow-hidden rounded-full border-4 border-white shadow-md dark:border-gray-700">
            <img
              src={croppedPreview}
              alt="Cropped Preview"
              className="h-full w-full object-cover"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AvatarCropper;
