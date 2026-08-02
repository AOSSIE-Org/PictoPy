import { useState, useCallback } from 'react';

interface ViewState {
  rotation: number;
}

export const useImageViewControls = () => {
  const [viewState, setViewState] = useState<ViewState>({
    rotation: 0,
  });

  const handleRotate = useCallback(() => {
    setViewState((prev) => ({
      rotation: (prev.rotation + 90) % 360,
    }));
  }, []);

  const resetZoom = useCallback(() => {
    setViewState({
      rotation: 0,
    });
  }, []);

  return {
    viewState,
    handlers: {
      handleRotate,
      resetZoom,
    },
  };
};
