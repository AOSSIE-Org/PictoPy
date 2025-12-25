import React, { useRef, useImperativeHandle, forwardRef } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { convertFileSrc } from '@tauri-apps/api/core';

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
    const transformRef = useRef<any>(null);

    // Expose zoom functions to parent
    useImperativeHandle(ref, () => ({
      zoomIn: () => transformRef.current?.zoomIn(),
      zoomOut: () => transformRef.current?.zoomOut(),
      reset: () => transformRef.current?.resetTransform(),
    }));

    // Reset on signal change
    React.useEffect(() => {
      transformRef.current?.resetTransform();
    }, [resetSignal]);

    return (
      <div style={{ width: '100%', height: '100%' }}>
        <TransformWrapper
          ref={transformRef}
          key={imagePath}
          initialScale={1}
          maxScale={10}
          wheel={{
            step: 0.15,
          }}
          centerOnInit
          limitToBounds={false}
        >
          <TransformComponent
            wrapperStyle={{
              width: '100%',
              height: '100%',
              overflow: 'visible',
            }}
            contentStyle={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <img
              src={convertFileSrc(imagePath) || '/placeholder.svg'}
              alt={alt}
              draggable={false}
              className="select-none"
              onError={(e) => {
                const img = e.target as HTMLImageElement;
                img.onerror = null;
                img.src = '/placeholder.svg';
              }}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'cover',
                zIndex: 50,
                transform: `rotate(${rotation}deg)`,
              }}
            />
          </TransformComponent>
        </TransformWrapper>
      </div>
    );
  },
);
