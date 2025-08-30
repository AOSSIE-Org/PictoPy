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
    <div
      id="zoomable-image"
      onClick={onClick}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseLeave}
      className="relative flex h-full w-full items-center justify-center overflow-hidden"
    >
      <img
        src={convertFileSrc(imagePath) || '/placeholder.svg'}
        alt={alt}
        draggable={false}
        className="h-full w-full object-contain select-none"
        onError={(e) => {
          const img = e.target as HTMLImageElement;
          img.onerror = null;
          img.src = '/placeholder.svg';
        }}
        style={{
          transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
          transition: isDragging ? 'none' : 'transform 0.2s ease-in-out',
          cursor: isDragging ? 'grabbing' : 'grab',
        }}
      />
    </div>
  );
};
