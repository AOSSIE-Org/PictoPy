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
  const handleWheelZoom = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const container = e.currentTarget.parentElement;
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    const mouseX = e.clientX - containerRect.left;
    const mouseY = e.clientY - containerRect.top;
    const deltaY = e.deltaY;
    setViewState((prev) => {
      const delta = deltaY > 0 ? -0.1 : 0.1;
      const newScale = Math.min(4, Math.max(0.5, prev.scale + delta));
      if (newScale === prev.scale) return prev;
      const scaleDiff = newScale - prev.scale;
      const newPosX =
        prev.position.x - (mouseX - prev.position.x) * (scaleDiff / prev.scale);
      const newPosY =
        prev.position.y - (mouseY - prev.position.y) * (scaleDiff / prev.scale);
      return {
        ...prev,
        scale: newScale,
        position: { x: newPosX, y: newPosY },
      };
    });
  }, []);

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
