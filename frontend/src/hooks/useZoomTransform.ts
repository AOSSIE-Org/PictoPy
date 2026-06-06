import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from 'react';
import {
  CONTROL_BUTTON_ZOOM_RATIO,
  LINE_HEIGHT_MULTIPLIER,
  MAX_FIT_RETRY_FRAMES,
  MAX_SCALE,
  MIN_SCALE,
  SCALE_EPSILON,
  WHEEL_ZOOM_SENSITIVITY,
  clamp,
  computeZoomTransform,
  getAxisPosition,
  getCenteredAxisPosition,
  getEffectiveDimensions,
  getElementSize,
  getFitTransform,
  getMinimumScale,
  getOverflowState,
  getScaledDimensions,
  type Geometry,
  type Size,
  type TransformState,
} from '@/utils/zoomUtils';

type UseZoomTransformParams = {
  imagePath: string;
  rotation: number;
  resetSignal?: number;
};

type DragState = {
  pointerId: number;
  startClientX: number;
  startClientY: number;
  startTransform: TransformState;
  geometry: Geometry;
};

export const useZoomTransform = ({
  imagePath,
  rotation,
  resetSignal,
}: UseZoomTransformParams) => {
  const viewportRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const transformStateRef = useRef<TransformState>({
    positionX: 0,
    positionY: 0,
    scale: MIN_SCALE,
  });
  const rawDimensionsRef = useRef<Size | null>(null);
  const isFitInitializedRef = useRef(false);
  const hasUserInteractedRef = useRef(false);
  const fitFrameRef = useRef<number | null>(null);
  const fitRetryCountRef = useRef(0);
  const dragStateRef = useRef<DragState | null>(null);
  const buttonZoomTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const rotationRef = useRef(rotation);
  const [transformState, setTransformState] = useState<TransformState>(
    transformStateRef.current,
  );
  const [rawDimensions, setRawDimensions] = useState<Size | null>(null);
  const [isOverflowing, setIsOverflowing] = useState(false);
  const [isPanning, setIsPanning] = useState(false);
  const [isButtonZoom, setIsButtonZoom] = useState(false);

  const setRawImageDimensions = useCallback((dimensions: Size | null) => {
    rawDimensionsRef.current = dimensions;
    setRawDimensions(dimensions);
  }, []);

  const readRawDimensions = useCallback((): Size | null => {
    const img = imageRef.current;
    const fallbackDimensions = rawDimensionsRef.current;

    if (img?.naturalWidth && img.naturalHeight) {
      return { width: img.naturalWidth, height: img.naturalHeight };
    }

    if (fallbackDimensions?.width && fallbackDimensions.height) {
      return fallbackDimensions;
    }

    if (img?.complete && img.clientWidth && img.clientHeight) {
      return { width: img.clientWidth, height: img.clientHeight };
    }

    return null;
  }, []);

  const getGeometry = useCallback((): Geometry | null => {
    const viewport = viewportRef.current;
    const rawImageDimensions = readRawDimensions();

    if (!viewport || !rawImageDimensions) return null;

    const viewportSize = getElementSize(viewport);

    if (!viewportSize.width || !viewportSize.height) return null;

    const baseDimensions = getEffectiveDimensions(
      rawImageDimensions.width,
      rawImageDimensions.height,
      rotationRef.current,
    );
    const minScale = getMinimumScale(
      baseDimensions,
      viewportSize.width,
      viewportSize.height,
    );

    return {
      viewportWidth: viewportSize.width,
      viewportHeight: viewportSize.height,
      viewportLeft: viewportSize.left,
      viewportTop: viewportSize.top,
      rawDimensions: rawImageDimensions,
      baseDimensions,
      minScale,
    };
  }, [readRawDimensions]);

  const setControlledTransform = useCallback(
    (nextTransform: TransformState) => {
      transformStateRef.current = nextTransform;
      setTransformState(nextTransform);
    },
    [],
  );

  const applyTransform = useCallback(
    (nextTransform: TransformState, geometry = getGeometry()) => {
      if (!geometry) return false;

      const scale = clamp(nextTransform.scale, geometry.minScale, MAX_SCALE);
      const scaledDimensions = getScaledDimensions(
        geometry.baseDimensions,
        scale,
      );
      const overflow = getOverflowState(
        geometry.baseDimensions,
        scale,
        geometry.viewportWidth,
        geometry.viewportHeight,
      );
      const shouldRecenter =
        scale <= geometry.minScale + SCALE_EPSILON ||
        (!overflow.width && !overflow.height);

      const positionX = shouldRecenter
        ? getCenteredAxisPosition(
            geometry.viewportWidth,
            scaledDimensions.width,
          )
        : getAxisPosition(
            nextTransform.positionX,
            geometry.viewportWidth,
            scaledDimensions.width,
            overflow.width,
          );
      const positionY = shouldRecenter
        ? getCenteredAxisPosition(
            geometry.viewportHeight,
            scaledDimensions.height,
          )
        : getAxisPosition(
            nextTransform.positionY,
            geometry.viewportHeight,
            scaledDimensions.height,
            overflow.height,
          );

      setIsOverflowing(overflow.width || overflow.height);
      setControlledTransform({ positionX, positionY, scale });
      return true;
    },
    [getGeometry, setControlledTransform],
  );

  const applyFitTransform = useCallback(() => {
    const geometry = getGeometry();

    if (!geometry) return false;

    const didApply = applyTransform(getFitTransform(geometry), geometry);

    if (didApply) {
      isFitInitializedRef.current = true;
      hasUserInteractedRef.current = false;
      fitRetryCountRef.current = 0;
    }

    return didApply;
  }, [applyTransform, getGeometry]);

  const clearScheduledFit = useCallback((resetRetryCount = true) => {
    if (resetRetryCount) {
      fitRetryCountRef.current = 0;
    }

    if (fitFrameRef.current === null) return;

    if (typeof window.cancelAnimationFrame === 'function') {
      window.cancelAnimationFrame(fitFrameRef.current);
    } else {
      window.clearTimeout(fitFrameRef.current);
    }
    fitFrameRef.current = null;
  }, []);

  const scheduleFitTransform = useCallback(
    (resetRetryCount = true) => {
      clearScheduledFit(resetRetryCount);

      const scheduleFrame: (callback: FrameRequestCallback) => number =
        typeof window.requestAnimationFrame === 'function'
          ? window.requestAnimationFrame.bind(window)
          : (callback) =>
              window.setTimeout(() => callback(performance.now()), 0);

      fitFrameRef.current = scheduleFrame(() => {
        fitFrameRef.current = null;
        const applied = applyFitTransform();

        if (!applied && fitRetryCountRef.current < MAX_FIT_RETRY_FRAMES) {
          fitRetryCountRef.current += 1;
          scheduleFitTransform(false);
        }
      });
    },
    [applyFitTransform, clearScheduledFit],
  );

  const clearButtonZoomAnimation = useCallback(() => {
    setIsButtonZoom(false);
    if (buttonZoomTimeoutRef.current !== null) {
      clearTimeout(buttonZoomTimeoutRef.current);
      buttonZoomTimeoutRef.current = null;
    }
  }, []);

  const resetToFit = useCallback(() => {
    clearButtonZoomAnimation();
    isFitInitializedRef.current = false;
    hasUserInteractedRef.current = false;
    fitRetryCountRef.current = 0;
    scheduleFitTransform(false);
  }, [clearButtonZoomAnimation, scheduleFitTransform]);

  const zoomBy = useCallback(
    (zoomRatio: number, clientX?: number, clientY?: number) => {
      const geometry = getGeometry();

      if (!geometry) return false;

      const currentTransform = isFitInitializedRef.current
        ? transformStateRef.current
        : getFitTransform(geometry);
      const didApply = applyTransform(
        computeZoomTransform({
          geometry,
          currentTransform,
          zoomRatio,
          clientX,
          clientY,
        }),
        geometry,
      );

      if (didApply) {
        isFitInitializedRef.current = true;
        hasUserInteractedRef.current = true;
      }

      return didApply;
    },
    [applyTransform, getGeometry],
  );

  useEffect(() => {
    rotationRef.current = rotation;
    resetToFit();
  }, [rotation, resetToFit]);

  useEffect(() => {
    resetToFit();
  }, [resetSignal, resetToFit]);

  useEffect(() => {
    setIsOverflowing(false);
    setRawImageDimensions(null);
    resetToFit();
  }, [imagePath, resetToFit, setRawImageDimensions]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const handleResize = () => {
      if (hasUserInteractedRef.current) {
        clearButtonZoomAnimation();
        applyTransform(transformStateRef.current);
      } else {
        resetToFit();
      }
    };

    let resizeObserver: ResizeObserver | null = null;

    if (typeof ResizeObserver === 'function') {
      resizeObserver = new ResizeObserver(handleResize);
      resizeObserver.observe(viewport);
    }

    window.addEventListener('resize', handleResize);

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, [applyTransform, clearButtonZoomAnimation, resetToFit]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();

      clearButtonZoomAnimation();

      const isLineMode = e.deltaMode === 1;
      const multiplier = isLineMode ? LINE_HEIGHT_MULTIPLIER : 1;
      const normalizedDelta = -e.deltaY * multiplier;
      const zoomRatio = Math.exp(normalizedDelta * WHEEL_ZOOM_SENSITIVITY);

      zoomBy(zoomRatio, e.clientX, e.clientY);
    };

    viewport.addEventListener('wheel', handleWheel, {
      passive: false,
      capture: true,
    });

    return () => {
      viewport.removeEventListener('wheel', handleWheel, true);
    };
  }, [clearButtonZoomAnimation, zoomBy]);

  useEffect(
    () => () => {
      clearScheduledFit();
      if (buttonZoomTimeoutRef.current !== null) {
        clearTimeout(buttonZoomTimeoutRef.current);
      }
    },
    [clearScheduledFit],
  );

  const handleImageLoad = useCallback(() => {
    const dimensions = readRawDimensions();

    if (dimensions) {
      setRawImageDimensions(dimensions);
    }

    resetToFit();
  }, [readRawDimensions, resetToFit, setRawImageDimensions]);

  const startDrag = useCallback(
    (pointerId: number, clientX: number, clientY: number) => {
      const geometry = getGeometry();
      if (!geometry || dragStateRef.current) return false;

      const overflow = getOverflowState(
        geometry.baseDimensions,
        transformStateRef.current.scale,
        geometry.viewportWidth,
        geometry.viewportHeight,
      );

      if (!overflow.width && !overflow.height) return false;

      clearButtonZoomAnimation();

      dragStateRef.current = {
        pointerId,
        startClientX: clientX,
        startClientY: clientY,
        startTransform: transformStateRef.current,
        geometry,
      };
      hasUserInteractedRef.current = true;
      setIsPanning(true);
      return true;
    },
    [clearButtonZoomAnimation, getGeometry],
  );

  const updateDrag = useCallback(
    (pointerId: number, clientX: number, clientY: number) => {
      const dragState = dragStateRef.current;
      if (!dragState || dragState.pointerId !== pointerId) return false;

      const deltaX = clientX - dragState.startClientX;
      const deltaY = clientY - dragState.startClientY;

      applyTransform(
        {
          positionX: dragState.startTransform.positionX + deltaX,
          positionY: dragState.startTransform.positionY + deltaY,
          scale: dragState.startTransform.scale,
        },
        dragState.geometry,
      );
      return true;
    },
    [applyTransform],
  );

  const endDrag = useCallback((pointerId: number) => {
    const dragState = dragStateRef.current;
    if (!dragState || dragState.pointerId !== pointerId) return false;

    dragStateRef.current = null;
    setIsPanning(false);
    return true;
  }, []);

  const handlePointerDown = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (e.button > 0 || (e.buttons && e.buttons !== 1)) return;

      const didStartDrag = startDrag(e.pointerId, e.clientX, e.clientY);
      if (!didStartDrag) return;

      try {
        e.currentTarget.setPointerCapture?.(e.pointerId);
      } catch {
        // Pointer capture is a best-effort guard; pointerleave is the fallback.
      }
      e.preventDefault();
    },
    [startDrag],
  );

  const handlePointerMove = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      const didUpdateDrag = updateDrag(e.pointerId, e.clientX, e.clientY);
      if (!didUpdateDrag) return;

      e.preventDefault();
    },
    [updateDrag],
  );

  const handlePointerEnd = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      const didEndDrag = endDrag(e.pointerId);
      if (!didEndDrag) return;

      try {
        e.currentTarget.releasePointerCapture?.(e.pointerId);
      } catch {
        // The pointer may already be released if capture was unavailable.
      }
    },
    [endDrag],
  );

  const handlePointerLeave = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (e.currentTarget.hasPointerCapture?.(e.pointerId)) return;

      endDrag(e.pointerId);
    },
    [endDrag],
  );

  const startButtonZoom = useCallback(
    (ratio: number) => {
      clearButtonZoomAnimation();

      const before = transformStateRef.current;
      const didApply = zoomBy(ratio);
      const after = transformStateRef.current;
      const didChange =
        didApply &&
        (Math.abs(after.scale - before.scale) > SCALE_EPSILON ||
          Math.abs(after.positionX - before.positionX) > SCALE_EPSILON ||
          Math.abs(after.positionY - before.positionY) > SCALE_EPSILON);

      if (!didChange) return;
      if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches)
        return;

      setIsButtonZoom(true);
      buttonZoomTimeoutRef.current = setTimeout(() => {
        setIsButtonZoom(false);
        buttonZoomTimeoutRef.current = null;
      }, 300);
    },
    [clearButtonZoomAnimation, zoomBy],
  );
  const zoomIn = useCallback(
    () => startButtonZoom(CONTROL_BUTTON_ZOOM_RATIO),
    [startButtonZoom],
  );
  const zoomOut = useCallback(
    () => startButtonZoom(1 / CONTROL_BUTTON_ZOOM_RATIO),
    [startButtonZoom],
  );
  const handleZoomTransitionEnd = clearButtonZoomAnimation;

  const contentDimensions = rawDimensions
    ? getEffectiveDimensions(
        rawDimensions.width,
        rawDimensions.height,
        rotation,
      )
    : null;
  const imageOffset =
    rawDimensions && contentDimensions
      ? {
          left: (contentDimensions.width - rawDimensions.width) / 2,
          top: (contentDimensions.height - rawDimensions.height) / 2,
        }
      : { left: 0, top: 0 };
  const cursor = isPanning ? 'grabbing' : isOverflowing ? 'move' : 'default';

  return {
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
    reset: resetToFit,
  };
};
