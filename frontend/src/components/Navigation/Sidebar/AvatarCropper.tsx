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
    <div className="flex flex-col items-center gap-4 p-4">
      <div className="relative h-64 w-64 bg-gray-800">
        <Cropper
          image={image}
          crop={crop}
          zoom={zoom}
          aspect={1}
          onCropChange={setCrop}
          onZoomChange={setZoom}
          onCropComplete={handleCropComplete}
          classes={{
            containerClassName: 'rounded',
            mediaClassName: 'rounded',
          }}
        />
      </div>

      <input
        type="range"
        min={1}
        max={3}
        step={0.1}
        value={zoom}
        onChange={(e) => setZoom(Number(e.target.value))}
        className="w-48"
      />

      <button
        onClick={handleCropImage}
        className="rounded bg-blue-500 px-4 py-2 text-white shadow hover:bg-blue-600"
      >
        Crop
      </button>

      {croppedPreview && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold">Cropped Preview:</h3>
          <img
            src={croppedPreview}
            alt="Cropped Preview"
            className="rounded mt-2 h-32 w-32 border object-cover shadow-md"
          />
        </div>
      )}
    </div>
  );
};

export default AvatarCropper;
