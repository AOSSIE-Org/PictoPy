import { convertFileSrc } from '@tauri-apps/api/core';
import React from 'react';

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
  onWheel?: (e: React.WheelEvent) => void;
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
  onWheel,
}) => {
  return (
    <div className="relative flex h-full w-full items-center justify-center overflow-hidden">
      <div
        id="zoomable-image"
        className="relative"
        onClick={onClick}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseLeave}
      >
        <img
          src={convertFileSrc(imagePath) || '/placeholder.svg'}
          alt={alt}
          draggable={false}
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            img.onerror = null;
            img.src = '/placeholder.svg';
          }}
          onWheel={onWheel}
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
            transformOrigin: '0 0',
            transition: isDragging ? 'none' : 'transform 0.2s ease-in-out',
            cursor: isDragging ? 'grabbing' : 'grab',
            maxWidth: '100%',
            maxHeight: '100%',
            userSelect: 'none',
            objectFit: 'contain',
            display: 'block',
          }}
        />
      </div>
    </div>
  );
};
