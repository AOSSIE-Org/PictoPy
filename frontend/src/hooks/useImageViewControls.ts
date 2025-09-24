import { useState, useCallback } from 'react';

interface ViewState {
  scale: number;
  position: { x: number; y: number };
  rotation: number;
  isDragging: boolean;
  dragStart: { x: number; y: number };
}

export const useImageViewControls = () => {
  const [viewState, setViewState] = useState<ViewState>({
    scale: 1,
    position: { x: 0, y: 0 },
    rotation: 0,
    isDragging: false,
    dragStart: { x: 0, y: 0 },
  });

  // handlewheel zoom
 const handleWheelZoom = useCallback(
  (e: React.WheelEvent, containerRect: DOMRect) => {
    e.preventDefault();

    setViewState((prev) => {
      const mouseX = e.clientX - containerRect.left;
      const mouseY = e.clientY - containerRect.top;
      const delta = e.deltaY < 0 ? 0.1 : -0.1;
      const newScale = Math.min(4, Math.max(0.5, prev.scale + delta));
      const scaleFactor = newScale / prev.scale;
      const newPosX = mouseX - (mouseX - prev.position.x) * scaleFactor;
      const newPosY = mouseY - (mouseY - prev.position.y) * scaleFactor;
      return {
        ...prev,
        scale: newScale,
        position: { x: newPosX, y: newPosY },
      };
    });
  },
  []
);


  const handleZoomIn = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      scale: Math.min(4, prev.scale + 0.1),
    }));
  }, []);

  const handleZoomOut = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      scale: Math.max(0.5, prev.scale - 0.1),
    }));
  }, []);

  const handleRotate = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      rotation: (prev.rotation + 90) % 360,
    }));
  }, []);

  const resetZoom = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      scale: 1,
      position: { x: 0, y: 0 },
      rotation: 0,
    }));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setViewState((prev) => ({
      ...prev,
      isDragging: true,
      dragStart: {
        x: e.clientX - prev.position.x,
        y: e.clientY - prev.position.y,
      },
    }));
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    setViewState((prev) => {
      if (!prev.isDragging) return prev;

      return {
        ...prev,
        position: {
          x: e.clientX - prev.dragStart.x,
          y: e.clientY - prev.dragStart.y,
        },
      };
    });
  }, []);

  const handleMouseUp = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      isDragging: false,
    }));
  }, []);

  return {
    viewState,
    handlers: {
      handleZoomIn,
      handleZoomOut,
      handleRotate,
      resetZoom,
      handleMouseDown,
      handleMouseMove,
      handleMouseUp,
      handleWheelZoom,
    },
  };
};
