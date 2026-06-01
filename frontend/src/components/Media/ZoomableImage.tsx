import {
  useRef,
  useImperativeHandle,
  forwardRef,
  useEffect,
  useState,
  useCallback,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from 'react';
import { convertFileSrc } from '@tauri-apps/api/core';

const ZOOM_FACTOR = 0.001;
const LINE_HEIGHT_MULTIPLIER = 33;
const MAX_SCALE = 8;
const MIN_SCALE = 1;
const SCALE_EPSILON = 0.0001;
const MAX_FIT_RETRY_FRAMES = 12;
const CONTROL_BUTTON_ZOOM_STEP = 0.5;

type Size = {
  width: number;
  height: number;
};

type OverflowState = {
  width: boolean;
  height: boolean;
};

type TransformState = {
  positionX: number;
  positionY: number;
  scale: number;
};

type Geometry = {
  viewportWidth: number;
  viewportHeight: number;
  rawDimensions: Size;
  baseDimensions: Size;
  minScale: number;
};

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

const getCenteredAxisPosition = (viewportSize: number, scaledSize: number) =>
  (viewportSize - scaledSize) / 2;

const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

const clampOverflowAxisPosition = (
  position: number,
  viewportSize: number,
  scaledSize: number,
) => {
  const minPosition = viewportSize - scaledSize;
  const maxPosition = 0;

  return clamp(position, minPosition, maxPosition);
};

const getAxisPosition = (
  anchoredPosition: number,
  viewportSize: number,
  scaledSize: number,
  isOverflowingAxis: boolean,
) => {
  const centeredPosition = getCenteredAxisPosition(viewportSize, scaledSize);

  return isOverflowingAxis
    ? clampOverflowAxisPosition(anchoredPosition, viewportSize, scaledSize)
    : centeredPosition;
};

const axisTouchesViewport = (scaledSize: number, viewportSize: number) =>
  scaledSize >= viewportSize - SCALE_EPSILON;

const getEffectiveDimensions = (
  width: number,
  height: number,
  rotation: number,
): Size => {
  const normalizedRotation = ((rotation % 360) + 360) % 360;
  const isRotated90or270 =
    normalizedRotation === 90 || normalizedRotation === 270;

  return isRotated90or270
    ? { width: height, height: width }
    : { width, height };
};

const getMinimumScale = (
  baseDimensions: Size,
  viewportWidth: number,
  viewportHeight: number,
) => {
  if (
    !baseDimensions.width ||
    !baseDimensions.height ||
    !viewportWidth ||
    !viewportHeight
  ) {
    return MIN_SCALE;
  }

  return Math.min(
    MIN_SCALE,
    viewportWidth / baseDimensions.width,
    viewportHeight / baseDimensions.height,
  );
};

const getNextViewportEdgeScale = (
  baseDimensions: Size,
  viewportWidth: number,
  viewportHeight: number,
  currentTouchesViewport: OverflowState,
) => {
  const edgeScales = [];

  if (!currentTouchesViewport.width) {
    edgeScales.push(viewportWidth / baseDimensions.width);
  }

  if (!currentTouchesViewport.height) {
    edgeScales.push(viewportHeight / baseDimensions.height);
  }

  if (!edgeScales.length) return null;

  return Math.min(
    MAX_SCALE,
    Math.max(
      getMinimumScale(baseDimensions, viewportWidth, viewportHeight),
      Math.min(...edgeScales),
    ),
  );
};

const getScaledDimensions = (baseDimensions: Size, scale: number): Size => ({
  width: baseDimensions.width * scale,
  height: baseDimensions.height * scale,
});

const getOverflowState = (
  baseDimensions: Size,
  scale: number,
  viewportWidth: number,
  viewportHeight: number,
): OverflowState => {
  const scaledDimensions = getScaledDimensions(baseDimensions, scale);

  return {
    width: scaledDimensions.width > viewportWidth,
    height: scaledDimensions.height > viewportHeight,
  };
};

const getFitTransform = ({
  baseDimensions,
  viewportWidth,
  viewportHeight,
  minScale,
}: Geometry): TransformState => {
  const scaledDimensions = getScaledDimensions(baseDimensions, minScale);

  return {
    positionX: getCenteredAxisPosition(viewportWidth, scaledDimensions.width),
    positionY: getCenteredAxisPosition(viewportHeight, scaledDimensions.height),
    scale: minScale,
  };
};

const getElementSize = (element: HTMLElement) => {
  const rect = element.getBoundingClientRect();

  return {
    width: rect.width || element.clientWidth,
    height: rect.height || element.clientHeight,
    left: rect.left,
    top: rect.top,
  };
};

export const ZoomableImage = forwardRef<ZoomableImageRef, ZoomableImageProps>(
  ({ imagePath, alt, rotation, resetSignal }, ref) => {
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
    const dragStateRef = useRef<{
      pointerId: number | 'mouse';
      startClientX: number;
      startClientY: number;
      startTransform: TransformState;
    } | null>(null);
    const rotationRef = useRef(rotation);
    const [transformState, setTransformState] = useState<TransformState>(
      transformStateRef.current,
    );
    const [rawDimensions, setRawDimensions] = useState<Size | null>(null);
    const [isOverflowing, setIsOverflowing] = useState(false);
    const [isPanning, setIsPanning] = useState(false);

    const setRawImageDimensions = useCallback((dimensions: Size | null) => {
      rawDimensionsRef.current = dimensions;
      setRawDimensions(dimensions);
    }, []);

    const readRawDimensions = useCallback((): Size | null => {
      const img = imageRef.current;
      const fallbackDimensions = rawDimensionsRef.current;

      const width =
        img?.naturalWidth || img?.clientWidth || fallbackDimensions?.width || 0;
      const height =
        img?.naturalHeight ||
        img?.clientHeight ||
        fallbackDimensions?.height ||
        0;

      if (!width || !height) return null;

      return { width, height };
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

    const clearScheduledFit = useCallback(() => {
      if (fitFrameRef.current === null) return;

      if (typeof window.cancelAnimationFrame === 'function') {
        window.cancelAnimationFrame(fitFrameRef.current);
      } else {
        window.clearTimeout(fitFrameRef.current);
      }
      fitFrameRef.current = null;
    }, []);

    const scheduleFitTransform = useCallback(() => {
      clearScheduledFit();

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
          scheduleFitTransform();
        }
      });
    }, [applyFitTransform, clearScheduledFit]);

    const resetToFit = useCallback(() => {
      isFitInitializedRef.current = false;
      hasUserInteractedRef.current = false;
      fitRetryCountRef.current = 0;
      scheduleFitTransform();
    }, [scheduleFitTransform]);

    const zoomBy = useCallback(
      (zoomChange: number, clientX?: number, clientY?: number) => {
        const geometry = getGeometry();
        const viewport = viewportRef.current;

        if (!geometry || !viewport) return false;

        const viewportSize = getElementSize(viewport);
        const fitTransform = getFitTransform(geometry);
        const currentTransform = isFitInitializedRef.current
          ? transformStateRef.current
          : fitTransform;
        const desiredScale = clamp(
          currentTransform.scale + zoomChange,
          geometry.minScale,
          MAX_SCALE,
        );
        const currentDimensions = getScaledDimensions(
          geometry.baseDimensions,
          currentTransform.scale,
        );
        const currentTouchesViewport = {
          width: axisTouchesViewport(
            currentDimensions.width,
            geometry.viewportWidth,
          ),
          height: axisTouchesViewport(
            currentDimensions.height,
            geometry.viewportHeight,
          ),
        };
        const isZoomingIn = desiredScale > currentTransform.scale;
        const nextViewportEdgeScale = getNextViewportEdgeScale(
          geometry.baseDimensions,
          geometry.viewportWidth,
          geometry.viewportHeight,
          currentTouchesViewport,
        );
        const scale =
          isZoomingIn &&
          nextViewportEdgeScale !== null &&
          desiredScale > nextViewportEdgeScale
            ? nextViewportEdgeScale
            : desiredScale;
        const scaledDimensions = getScaledDimensions(
          geometry.baseDimensions,
          scale,
        );
        const newOverflow = getOverflowState(
          geometry.baseDimensions,
          scale,
          geometry.viewportWidth,
          geometry.viewportHeight,
        );
        const mouseViewportX =
          clientX === undefined
            ? geometry.viewportWidth / 2
            : clientX - viewportSize.left;
        const mouseViewportY =
          clientY === undefined
            ? geometry.viewportHeight / 2
            : clientY - viewportSize.top;
        const isOverImage =
          mouseViewportX >= currentTransform.positionX &&
          mouseViewportX <=
            currentTransform.positionX + currentDimensions.width &&
          mouseViewportY >= currentTransform.positionY &&
          mouseViewportY <=
            currentTransform.positionY + currentDimensions.height;
        const ratio =
          currentTransform.scale > 0 ? scale / currentTransform.scale : 1;
        const anchoredX =
          mouseViewportX -
          (mouseViewportX - currentTransform.positionX) * ratio;
        const anchoredY =
          mouseViewportY -
          (mouseViewportY - currentTransform.positionY) * ratio;
        const centeredX = getCenteredAxisPosition(
          geometry.viewportWidth,
          scaledDimensions.width,
        );
        const centeredY = getCenteredAxisPosition(
          geometry.viewportHeight,
          scaledDimensions.height,
        );
        const shouldAnchorX =
          isOverImage && currentTouchesViewport.width && newOverflow.width;
        const shouldAnchorY =
          isOverImage && currentTouchesViewport.height && newOverflow.height;

        const didApply = applyTransform(
          {
            positionX: shouldAnchorX ? anchoredX : centeredX,
            positionY: shouldAnchorY ? anchoredY : centeredY,
            scale,
          },
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

    useImperativeHandle(ref, () => ({
      zoomIn: () => {
        zoomBy(CONTROL_BUTTON_ZOOM_STEP);
      },
      zoomOut: () => {
        zoomBy(-CONTROL_BUTTON_ZOOM_STEP);
      },
      reset: () => resetToFit(),
    }));

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
    }, [applyTransform, resetToFit]);

    useEffect(() => {
      const viewport = viewportRef.current;
      if (!viewport) return;

      const handleWheel = (e: WheelEvent) => {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        const isLineMode = e.deltaMode === 1;
        const multiplier = isLineMode ? LINE_HEIGHT_MULTIPLIER : 1;
        const zoomChange = -e.deltaY * multiplier * ZOOM_FACTOR;

        zoomBy(zoomChange, e.clientX, e.clientY);
      };

      viewport.addEventListener('wheel', handleWheel, {
        passive: false,
        capture: true,
      });

      return () => {
        viewport.removeEventListener('wheel', handleWheel, true);
      };
    }, [zoomBy]);

    useEffect(
      () => () => {
        clearScheduledFit();
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
      (pointerId: number | 'mouse', clientX: number, clientY: number) => {
        const geometry = getGeometry();
        if (!geometry || dragStateRef.current) return false;

        const overflow = getOverflowState(
          geometry.baseDimensions,
          transformStateRef.current.scale,
          geometry.viewportWidth,
          geometry.viewportHeight,
        );

        if (!overflow.width && !overflow.height) return false;

        dragStateRef.current = {
          pointerId,
          startClientX: clientX,
          startClientY: clientY,
          startTransform: transformStateRef.current,
        };
        hasUserInteractedRef.current = true;
        setIsPanning(true);
        return true;
      },
      [getGeometry],
    );

    const updateDrag = useCallback(
      (pointerId: number | 'mouse', clientX: number, clientY: number) => {
        const dragState = dragStateRef.current;
        if (!dragState || dragState.pointerId !== pointerId) return false;

        const deltaX = clientX - dragState.startClientX;
        const deltaY = clientY - dragState.startClientY;

        applyTransform({
          positionX: dragState.startTransform.positionX + deltaX,
          positionY: dragState.startTransform.positionY + deltaY,
          scale: dragState.startTransform.scale,
        });
        return true;
      },
      [applyTransform],
    );

    const endDrag = useCallback((pointerId: number | 'mouse') => {
      const dragState = dragStateRef.current;
      if (!dragState || dragState.pointerId !== pointerId) return false;

      dragStateRef.current = null;
      setIsPanning(false);
      return true;
    }, []);

    const handlePointerDown = (e: ReactPointerEvent<HTMLDivElement>) => {
      if (e.button !== 0) return;

      const didStartDrag = startDrag(e.pointerId, e.clientX, e.clientY);
      if (!didStartDrag) return;

      e.currentTarget.setPointerCapture?.(e.pointerId);
      e.preventDefault();
    };

    const handlePointerMove = (e: ReactPointerEvent<HTMLDivElement>) => {
      const didUpdateDrag = updateDrag(e.pointerId, e.clientX, e.clientY);
      if (!didUpdateDrag) return;

      e.preventDefault();
    };

    const handlePointerEnd = (e: ReactPointerEvent<HTMLDivElement>) => {
      const didEndDrag = endDrag(e.pointerId);
      if (!didEndDrag) return;

      e.currentTarget.releasePointerCapture?.(e.pointerId);
    };

    const handleMouseDown = (e: ReactMouseEvent<HTMLDivElement>) => {
      if (e.button !== 0) return;

      const didStartDrag = startDrag('mouse', e.clientX, e.clientY);
      if (didStartDrag) {
        e.preventDefault();
      }
    };

    const handleMouseMove = (e: ReactMouseEvent<HTMLDivElement>) => {
      const didUpdateDrag = updateDrag('mouse', e.clientX, e.clientY);
      if (didUpdateDrag) {
        e.preventDefault();
      }
    };

    const handleMouseEnd = () => {
      endDrag('mouse');
    };

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

    return (
      <div
        ref={viewportRef}
        data-testid="zoom-viewport"
        className="h-full w-full overflow-hidden select-none"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerEnd}
        onPointerCancel={handlePointerEnd}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseEnd}
        onMouseLeave={handleMouseEnd}
        style={{
          touchAction: 'none',
          cursor: isPanning ? 'grabbing' : isOverflowing ? 'move' : 'default',
        }}
      >
        <div
          data-testid="zoom-content"
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
            cursor: isPanning ? 'grabbing' : isOverflowing ? 'move' : 'default',
            willChange: 'transform',
          }}
        >
          <img
            key={imagePath}
            ref={imageRef}
            src={convertFileSrc(imagePath) || '/placeholder.svg'}
            alt={alt}
            draggable={false}
            className="select-none"
            onLoad={handleImageLoad}
            onError={(e) => {
              const img = e.target as HTMLImageElement;
              img.onerror = null;
              img.src = '/placeholder.svg';
            }}
            style={{
              position: contentDimensions ? 'absolute' : 'relative',
              left: `${imageOffset.left}px`,
              top: `${imageOffset.top}px`,
              width: rawDimensions ? `${rawDimensions.width}px` : undefined,
              height: rawDimensions ? `${rawDimensions.height}px` : undefined,
              maxWidth: 'none',
              maxHeight: 'none',
              objectFit: 'contain',
              zIndex: 50,
              transform: `rotate(${rotation}deg)`,
              transformOrigin: 'center center',
              cursor: isPanning
                ? 'grabbing'
                : isOverflowing
                  ? 'move'
                  : 'default',
              pointerEvents: 'none',
            }}
          />
        </div>
      </div>
    );
  },
);

ZoomableImage.displayName = 'ZoomableImage';
