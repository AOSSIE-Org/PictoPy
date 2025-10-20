import { convertFileSrc } from '@tauri-apps/api/core';
import React from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

interface ImageViewerProps {
  imagePath: string;
  alt: string;
  scale: number;
  position: { x: number; y: number };
  rotation: number;
  isDragging: boolean;
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseMove: (e: React.MouseEvent) => void;
  onMouseUp: () => void;
  onMouseLeave: () => void;
  onClick?: (e: React.MouseEvent) => void;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({
  imagePath,
  alt,
  scale,
  position,
  rotation,
  isDragging,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  onMouseLeave,
  onClick,
}) => {
  return (
    <TransformWrapper
      initialScale={1}
      minScale={0.1}
      maxScale={8}
      centerOnInit={true}
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
          onClick={onClick}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseLeave}
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
            objectFit: 'contain',
            // transform: `rotate(${rotation}deg)`,
            zIndex: 50,
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
            transition: isDragging ? 'none' : 'transform 0.2s ease-in-out',
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        />
      </TransformComponent>
    </TransformWrapper>
  );
};
