import { useImperativeHandle, forwardRef } from 'react';
import { convertFileSrc } from '@tauri-apps/api/core';
import { useZoomTransform } from '@/hooks/useZoomTransform';

interface ZoomableImageProps {
  imagePath: string;
  alt: string;
  rotation: number;
  resetSignal?: number;
}

export interface ZoomableImageRef {
  zoomIn: () => void;
  zoomOut: () => void;
  reset: () => void;
}

export const ZoomableImage = forwardRef<ZoomableImageRef, ZoomableImageProps>(
  ({ imagePath, alt, rotation, resetSignal }, ref) => {
    const {
      viewportRef,
      imageRef,
      transformState,
      rawDimensions,
      contentDimensions,
      imageOffset,
      cursor,
      handleImageLoad,
      handlePointerDown,
      handlePointerMove,
      handlePointerEnd,
      handlePointerLeave,
      zoomIn,
      zoomOut,
      reset,
    } = useZoomTransform({ imagePath, rotation, resetSignal });

    useImperativeHandle(ref, () => ({
      zoomIn,
      zoomOut,
      reset,
    }));

    return (
      <div
        ref={viewportRef}
        data-testid="zoom-viewport"
        className="h-full w-full overflow-hidden select-none"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerEnd}
        onPointerCancel={handlePointerEnd}
        onPointerLeave={handlePointerLeave}
        onLostPointerCapture={handlePointerEnd}
        style={{
          touchAction: 'none',
          cursor,
        }}
      >
        <div
          data-testid="zoom-content"
          style={{
            position: 'relative',
            width: contentDimensions
              ? `${contentDimensions.width}px`
              : 'fit-content',
            height: contentDimensions
              ? `${contentDimensions.height}px`
              : 'fit-content',
            transform: `translate3d(${transformState.positionX}px, ${transformState.positionY}px, 0) scale(${transformState.scale})`,
            transformOrigin: '0 0',
            willChange: 'transform',
          }}
        >
          <img
            key={imagePath}
            ref={imageRef}
            src={convertFileSrc(imagePath) || '/placeholder.svg'}
            alt={alt}
            draggable={false}
            className="select-none"
            onLoad={handleImageLoad}
            onError={(e) => {
              const img = e.target as HTMLImageElement;
              img.onerror = null;
              img.src = '/placeholder.svg';
            }}
            style={{
              position: contentDimensions ? 'absolute' : 'relative',
              left: `${imageOffset.left}px`,
              top: `${imageOffset.top}px`,
              width: rawDimensions ? `${rawDimensions.width}px` : undefined,
              height: rawDimensions ? `${rawDimensions.height}px` : undefined,
              maxWidth: 'none',
              maxHeight: 'none',
              objectFit: 'contain',
              zIndex: 50,
              transform: `rotate(${rotation}deg)`,
              transformOrigin: 'center center',
              pointerEvents: 'none',
            }}
          />
        </div>
      </div>
    );
  },
);

ZoomableImage.displayName = 'ZoomableImage';
