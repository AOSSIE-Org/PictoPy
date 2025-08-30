import { useEffect, useCallback } from 'react';

interface KeyboardHandlers {
  onClose: () => void;
  onNext: () => void;
  onPrevious: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRotate: () => void;
  onToggleInfo: () => void;
}

export const useKeyboardNavigation = (handlers: KeyboardHandlers) => {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          handlers.onClose();
          break;
        case 'ArrowRight':
          handlers.onNext();
          break;
        case 'ArrowLeft':
          handlers.onPrevious();
          break;
        case '+':
        case '=':
          handlers.onZoomIn();
          break;
        case '-':
          handlers.onZoomOut();
          break;
        case 'r':
        case 'R':
          handlers.onRotate();
          break;
        case 'i':
        case 'I':
          handlers.onToggleInfo();
          break;
      }
    },
    [handlers],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
};
