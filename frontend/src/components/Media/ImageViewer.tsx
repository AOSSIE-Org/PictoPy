import { useRef, useImperativeHandle, forwardRef } from 'react';
import { ZoomableImage, ZoomableImageRef } from './ZoomableImage';

interface ImageViewerProps {
  imagePath: string;
  alt: string;
  rotation: number;
  resetSignal?: number;
}

export interface ImageViewerRef {
  zoomIn: () => void;
  zoomOut: () => void;
  reset: () => void;
}

export const ImageViewer = forwardRef<ImageViewerRef, ImageViewerProps>(
  ({ imagePath, alt, rotation, resetSignal }, ref) => {
    const zoomableImageRef = useRef<ZoomableImageRef>(null);

    useImperativeHandle(ref, () => ({
      zoomIn: () => zoomableImageRef.current?.zoomIn(),
      zoomOut: () => zoomableImageRef.current?.zoomOut(),
      reset: () => zoomableImageRef.current?.reset(),
    }));

    return (
      <ZoomableImage
        ref={zoomableImageRef}
        imagePath={imagePath}
        alt={alt}
        rotation={rotation}
        resetSignal={resetSignal}
      />
    );
  },
);
