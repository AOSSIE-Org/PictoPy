import React, { useState, useCallback } from "react";
import Cropper from "react-easy-crop";

interface AvatarCropperProps {
  image: string;
  onCropComplete: (croppedImage: string) => void;
}

const AvatarCropper: React.FC<AvatarCropperProps> = ({ image, onCropComplete }) => {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);
  const [croppedPreview, setCroppedPreview] = useState<string | null>(null);

  const handleCropComplete = useCallback((_, croppedAreaPixels) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const createImage = (url: string): Promise<HTMLImageElement> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.src = url;
      img.onload = () => resolve(img);
      img.onerror = (error) => reject(error);
    });
  };

  const getCroppedImg = async (imageSrc: string, crop) => {
    const image = await createImage(imageSrc);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

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
      crop.height
    );

    return canvas.toDataURL("image/jpeg");
  };

  const handleCropImage = async () => {
    if (croppedAreaPixels) {
      try {
        const croppedImage = await getCroppedImg(image, croppedAreaPixels);
        onCropComplete(croppedImage);
        setCroppedPreview(croppedImage);
      } catch (error) {
        console.error("Cropping failed:", error);
      }
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <div className="relative w-64 h-64 bg-gray-800">
        <Cropper
          image={image}
          crop={crop}
          zoom={zoom}
          aspect={1}
          onCropChange={setCrop}
          onZoomChange={setZoom}
          onCropComplete={handleCropComplete}
          classes={{
            containerClassName: "rounded",
            mediaClassName: "rounded",
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
        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded shadow"
      >
        Crop
      </button>

      {croppedPreview && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold">Cropped Preview:</h3>
          <img
            src={croppedPreview}
            alt="Cropped Preview"
            className="border rounded shadow-md mt-2 w-32 h-32 object-cover"
          />
        </div>
      )}
    </div>
  );
};

export default AvatarCropper;