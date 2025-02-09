export const getCroppedImg = (imageSrc: string, crop: any): Promise<string> => {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.src = imageSrc;
    image.crossOrigin = 'anonymous'; // Add this if loading external images

    image.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      if (!ctx) return reject('Canvas context not found');

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

      canvas.toBlob((blob) => {
        if (blob) {
          const croppedImageUrl = URL.createObjectURL(blob);
          resolve(croppedImageUrl);
        } else {
          reject('Failed to create blob');
        }
      }, 'image/jpeg');
    };

    image.onerror = () => reject('Failed to load image');
  });
};
