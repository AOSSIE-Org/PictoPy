import { useImperativeHandle, forwardRef } from 'react';
import { convertFileSrc } from '@tauri-apps/api/core';
import { useZoomTransform } from '@/hooks/useZoomTransform';
import {
  PLACEHOLDER_IMAGE_SRC,
  handlePlaceholderImageError,
} from '@/utils/imageFallback';

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
      isButtonZoom,
      handleImageLoad,
      handlePointerDown,
      handlePointerMove,
      handlePointerEnd,
      handlePointerLeave,
      handleZoomTransitionEnd,
      zoomIn,
      zoomOut,
      reset,
    } = useZoomTransform({ imagePath, rotation, resetSignal });

    useImperativeHandle(
      ref,
      () => ({
        zoomIn,
        zoomOut,
        reset,
      }),
      [zoomIn, zoomOut, reset],
    );

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
          onTransitionEnd={(e) => {
            if (
              e.target === e.currentTarget &&
              e.propertyName === 'transform'
            ) {
              handleZoomTransitionEnd();
            }
          }}
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
            transition: isButtonZoom ? 'transform 250ms ease-out' : undefined,
          }}
        >
          <img
            key={imagePath}
            ref={imageRef}
            src={convertFileSrc(imagePath) || PLACEHOLDER_IMAGE_SRC}
            alt={alt}
            draggable={false}
            onLoad={handleImageLoad}
            onError={handlePlaceholderImageError}
            style={{
              position: contentDimensions ? 'absolute' : 'relative',
              left: `${imageOffset.left}px`,
              top: `${imageOffset.top}px`,
              width: rawDimensions ? `${rawDimensions.width}px` : undefined,
              height: rawDimensions ? `${rawDimensions.height}px` : undefined,
              // Override the framework's `img { max-width: 100% }` reset so the
              // image can scale beyond the viewport while zoomed.
              maxWidth: 'none',
              maxHeight: 'none',
              objectFit: 'contain',
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
