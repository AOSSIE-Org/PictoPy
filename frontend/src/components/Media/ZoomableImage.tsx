import {
  useRef,
  useImperativeHandle,
  forwardRef,
  useEffect,
  useState,
  useCallback,
} from 'react';
import {
  TransformWrapper,
  TransformComponent,
  ReactZoomPanPinchRef,
} from 'react-zoom-pan-pinch';
import { convertFileSrc } from '@tauri-apps/api/core';

const ZOOM_FACTOR = 0.001;
const LINE_HEIGHT_MULTIPLIER = 33;
const MAX_SCALE = 8;
const MIN_SCALE = 1;
const SCALE_EPSILON = 0.0001;
const MAX_FIT_RETRY_FRAMES = 12;

type Size = {
  width: number;
  height: number;
};

type OverflowState = {
  width: boolean;
  height: boolean;
};

type FitTransform = {
  positionX: number;
  positionY: number;
  scale: number;
};

type AnimationType =
  | 'easeOut'
  | 'linear'
  | 'easeInQuad'
  | 'easeOutQuad'
  | 'easeInOutQuad'
  | 'easeInCubic'
  | 'easeOutCubic'
  | 'easeInOutCubic'
  | 'easeInQuart'
  | 'easeOutQuart'
  | 'easeInOutQuart'
  | 'easeInQuint'
  | 'easeOutQuint'
  | 'easeInOutQuint';

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

const getFirstViewportEdgeScale = (
  baseDimensions: Size,
  viewportWidth: number,
  viewportHeight: number,
) =>
  Math.min(
    MAX_SCALE,
    Math.max(
      getMinimumScale(baseDimensions, viewportWidth, viewportHeight),
      Math.min(
        viewportWidth / baseDimensions.width,
        viewportHeight / baseDimensions.height,
      ),
    ),
  );

const getFitTransform = (
  baseDimensions: Size,
  viewportWidth: number,
  viewportHeight: number,
): FitTransform | null => {
  if (!viewportWidth || !viewportHeight) return null;

  const scale = getMinimumScale(baseDimensions, viewportWidth, viewportHeight);
  const scaledWidth = baseDimensions.width * scale;
  const scaledHeight = baseDimensions.height * scale;

  return {
    positionX: getCenteredAxisPosition(viewportWidth, scaledWidth),
    positionY: getCenteredAxisPosition(viewportHeight, scaledHeight),
    scale,
  };
};

export const ZoomableImage = forwardRef<ZoomableImageRef, ZoomableImageProps>(
  ({ imagePath, alt, rotation, resetSignal }, ref) => {
    const transformRef = useRef<ReactZoomPanPinchRef>(null);
    const wheelAreaRef = useRef<HTMLDivElement>(null);
    const imageRef = useRef<HTMLImageElement>(null);
    const isFitInitializedRef = useRef(false);
    const hasUserInteractedRef = useRef(false);
    const hasPendingFitRef = useRef(true);
    const fitTransformRef = useRef<FitTransform | null>(null);
    const fitFrameRef = useRef<number | null>(null);
    const fitRetryCountRef = useRef(0);
    const [isOverflowing, setIsOverflowing] = useState(false);
    const [minScale, setMinScale] = useState(MIN_SCALE);
    const rotationRef = useRef(rotation);

    const setMinimumScale = useCallback((scale: number) => {
      setMinScale((currentScale) =>
        Math.abs(currentScale - scale) < SCALE_EPSILON ? currentScale : scale,
      );
    }, []);

    const getEffectiveDimensions = useCallback(
      (width: number, height: number) => {
        const normalizedRotation = ((rotationRef.current % 360) + 360) % 360;
        const isRotated90or270 =
          normalizedRotation === 90 || normalizedRotation === 270;
        return isRotated90or270
          ? { width: height, height: width }
          : { width, height };
      },
      [],
    );

    const getBaseDimensions = useCallback((): Size | null => {
      if (!imageRef.current) return null;

      const renderedWidth =
        imageRef.current.naturalWidth || imageRef.current.clientWidth;
      const renderedHeight =
        imageRef.current.naturalHeight || imageRef.current.clientHeight;

      if (!renderedWidth || !renderedHeight) return null;

      return getEffectiveDimensions(renderedWidth, renderedHeight);
    }, [getEffectiveDimensions]);

    const getScaledDimensions = useCallback(
      (scale: number): Size | null => {
        const baseDimensions = getBaseDimensions();

        if (!baseDimensions) return null;

        return {
          width: baseDimensions.width * scale,
          height: baseDimensions.height * scale,
        };
      },
      [getBaseDimensions],
    );

    const getOverflowState = useCallback(
      (
        scale: number,
        viewportWidth: number,
        viewportHeight: number,
      ): OverflowState => {
        const scaledDimensions = getScaledDimensions(scale);

        if (!scaledDimensions) return { width: false, height: false };

        return {
          width: scaledDimensions.width > viewportWidth,
          height: scaledDimensions.height > viewportHeight,
        };
      },
      [getScaledDimensions],
    );

    const getViewportElement = useCallback(
      () =>
        transformRef.current?.instance?.wrapperComponent ??
        wheelAreaRef.current,
      [],
    );

    const clearScheduledFit = useCallback(() => {
      if (fitFrameRef.current === null) return;

      if (typeof window.cancelAnimationFrame === 'function') {
        window.cancelAnimationFrame(fitFrameRef.current);
      } else {
        window.clearTimeout(fitFrameRef.current);
      }
      fitFrameRef.current = null;
    }, []);

    const markFitPending = useCallback(() => {
      isFitInitializedRef.current = false;
      hasUserInteractedRef.current = false;
      hasPendingFitRef.current = true;
      fitTransformRef.current = null;
      fitRetryCountRef.current = 0;
    }, []);

    const applyFitTransform = useCallback(
      (duration = 200, animationType: AnimationType = 'easeOut') => {
        const transform = transformRef.current;
        const contentElement = transform?.instance?.contentComponent;
        const viewportElement = getViewportElement();
        if (
          !transform ||
          !contentElement ||
          !viewportElement ||
          !imageRef.current
        )
          return false;

        const wrapperRect = viewportElement.getBoundingClientRect();
        if (!wrapperRect.width || !wrapperRect.height) return false;

        const baseDimensions = getBaseDimensions();

        if (!baseDimensions) return false;

        const fitTransform = getFitTransform(
          baseDimensions,
          wrapperRect.width,
          wrapperRect.height,
        );

        if (!fitTransform) return false;

        fitTransformRef.current = fitTransform;
        isFitInitializedRef.current = true;
        hasUserInteractedRef.current = false;
        hasPendingFitRef.current = false;
        fitRetryCountRef.current = 0;
        setMinimumScale(fitTransform.scale);
        transform.setTransform(
          fitTransform.positionX,
          fitTransform.positionY,
          fitTransform.scale,
          duration,
          animationType,
        );
        setIsOverflowing(false);
        return true;
      },
      [getBaseDimensions, getViewportElement, setMinimumScale],
    );

    const scheduleFitTransform = useCallback(
      (duration = 200, animationType: AnimationType = 'easeOut') => {
        clearScheduledFit();

        const scheduleFrame: (callback: FrameRequestCallback) => number =
          typeof window.requestAnimationFrame === 'function'
            ? window.requestAnimationFrame.bind(window)
            : (callback) =>
                window.setTimeout(() => callback(performance.now()), 0);

        fitFrameRef.current = scheduleFrame(() => {
          fitFrameRef.current = null;
          const applied = applyFitTransform(duration, animationType);

          if (
            !applied &&
            hasPendingFitRef.current &&
            fitRetryCountRef.current < MAX_FIT_RETRY_FRAMES
          ) {
            fitRetryCountRef.current += 1;
            scheduleFitTransform(duration, animationType);
          }
        });
      },
      [applyFitTransform, clearScheduledFit],
    );

    const handleReset = useCallback(
      (duration = 200, animationType: AnimationType = 'easeOut') => {
        markFitPending();
        scheduleFitTransform(duration, animationType);
      },
      [markFitPending, scheduleFitTransform],
    );

    useImperativeHandle(ref, () => ({
      zoomIn: () => {
        hasUserInteractedRef.current = true;
        transformRef.current?.zoomIn();
      },
      zoomOut: () => {
        hasUserInteractedRef.current = true;
        transformRef.current?.zoomOut();
      },
      reset: () => handleReset(),
    }));

    useEffect(() => {
      handleReset();
    }, [resetSignal, handleReset]);

    useEffect(() => {
      rotationRef.current = rotation;
      markFitPending();
      scheduleFitTransform(0);
    }, [rotation, markFitPending, scheduleFitTransform]);

    useEffect(() => {
      const viewportElement = getViewportElement();
      if (!transformRef.current || !viewportElement || !imageRef.current)
        return;

      const scale = transformRef.current.instance.transformState.scale;
      const rect = viewportElement.getBoundingClientRect();
      const baseDimensions = getBaseDimensions();

      if (baseDimensions) {
        setMinimumScale(
          getMinimumScale(baseDimensions, rect.width, rect.height),
        );
      }

      const overflow = getOverflowState(scale, rect.width, rect.height);
      setIsOverflowing(overflow.width || overflow.height);
    }, [
      rotation,
      getBaseDimensions,
      getOverflowState,
      getViewportElement,
      setMinimumScale,
    ]);

    useEffect(() => {
      setIsOverflowing(false);
      markFitPending();

      const img = imageRef.current;
      if (!img) return;

      if (img.complete && img.naturalWidth > 0) {
        scheduleFitTransform(0);
      }
    }, [imagePath, markFitPending, scheduleFitTransform]);

    const handleImageLoad = useCallback(() => {
      markFitPending();
      scheduleFitTransform(0);
    }, [markFitPending, scheduleFitTransform]);

    useEffect(() => {
      const wheelElement = wheelAreaRef.current;
      if (!wheelElement) return;

      let cachedViewportRect =
        getViewportElement()?.getBoundingClientRect() ??
        wheelElement.getBoundingClientRect();

      const resizeObserver = new ResizeObserver(() => {
        const viewportElement = getViewportElement() ?? wheelElement;

        cachedViewportRect = viewportElement.getBoundingClientRect();

        const baseDimensions = getBaseDimensions();
        if (baseDimensions) {
          const fitTransform = getFitTransform(
            baseDimensions,
            cachedViewportRect.width,
            cachedViewportRect.height,
          );

          if (fitTransform) {
            fitTransformRef.current = fitTransform;
            setMinimumScale(fitTransform.scale);

            if (!hasUserInteractedRef.current) {
              scheduleFitTransform(0);
            }
          }
        }
      });

      resizeObserver.observe(wheelElement);

      const handleWheelInterceptor = (e: WheelEvent) => {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        if (!imageRef.current || !transformRef.current) return;
        if (!transformRef.current.instance.contentComponent) {
          scheduleFitTransform(0);
          return;
        }

        clearScheduledFit();

        const transformState = transformRef.current.instance.transformState;
        const viewportElement = getViewportElement() ?? wheelElement;

        cachedViewportRect = viewportElement.getBoundingClientRect();
        const viewportRect = cachedViewportRect;
        const imageRect = imageRef.current.getBoundingClientRect();
        const mouseX = e.clientX - imageRect.left;
        const mouseY = e.clientY - imageRect.top;

        const isOverImage =
          mouseX >= 0 &&
          mouseX <= imageRect.width &&
          mouseY >= 0 &&
          mouseY <= imageRect.height;

        const isLineMode = e.deltaMode === 1;
        const multiplier = isLineMode ? LINE_HEIGHT_MULTIPLIER : 1;
        const factor = ZOOM_FACTOR;

        const zoomChange = -e.deltaY * multiplier * factor;

        const baseDimensions = getBaseDimensions();
        if (!baseDimensions) return;

        const fitTransform = getFitTransform(
          baseDimensions,
          viewportRect.width,
          viewportRect.height,
        );
        if (!fitTransform) return;

        const minimumScale = getMinimumScale(
          baseDimensions,
          viewportRect.width,
          viewportRect.height,
        );
        fitTransformRef.current = fitTransform;

        const shouldUseFitTransform =
          hasPendingFitRef.current || !isFitInitializedRef.current;
        const currentScale = shouldUseFitTransform
          ? fitTransform.scale
          : transformState.scale;
        const currentPositionX = shouldUseFitTransform
          ? fitTransform.positionX
          : transformState.positionX;
        const currentPositionY = shouldUseFitTransform
          ? fitTransform.positionY
          : transformState.positionY;
        const desiredScale = Math.max(
          minimumScale,
          Math.min(MAX_SCALE, currentScale + zoomChange),
        );
        setMinimumScale(minimumScale);

        const currentDimensions = {
          width: baseDimensions.width * currentScale,
          height: baseDimensions.height * currentScale,
        };
        const currentTouchesViewport = {
          width: axisTouchesViewport(
            currentDimensions.width,
            viewportRect.width,
          ),
          height: axisTouchesViewport(
            currentDimensions.height,
            viewportRect.height,
          ),
        };
        const isZoomingIn = desiredScale > currentScale;

        const shouldFitFirst =
          isZoomingIn &&
          !currentTouchesViewport.width &&
          !currentTouchesViewport.height;
        const firstViewportEdgeScale = getFirstViewportEdgeScale(
          baseDimensions,
          viewportRect.width,
          viewportRect.height,
        );
        const newScale =
          shouldFitFirst && desiredScale > firstViewportEdgeScale
            ? firstViewportEdgeScale
            : desiredScale;

        const scaledDimensions = getScaledDimensions(newScale);
        if (!scaledDimensions) return;

        const newOverflow = getOverflowState(
          newScale,
          viewportRect.width,
          viewportRect.height,
        );

        const shouldRecenter =
          newScale <= minimumScale + SCALE_EPSILON ||
          (!newOverflow.width && !newOverflow.height);

        const centeredX = getCenteredAxisPosition(
          viewportRect.width,
          scaledDimensions.width,
        );
        const centeredY = getCenteredAxisPosition(
          viewportRect.height,
          scaledDimensions.height,
        );
        const ratio = currentScale > 0 ? newScale / currentScale : 1;
        const mouseViewportX = e.clientX - viewportRect.left;
        const mouseViewportY = e.clientY - viewportRect.top;
        const anchoredX =
          mouseViewportX - (mouseViewportX - currentPositionX) * ratio;
        const anchoredY =
          mouseViewportY - (mouseViewportY - currentPositionY) * ratio;
        const shouldAnchorX =
          isOverImage && currentTouchesViewport.width && newOverflow.width;
        const shouldAnchorY =
          isOverImage && currentTouchesViewport.height && newOverflow.height;

        const targetX = shouldRecenter
          ? centeredX
          : getAxisPosition(
              shouldAnchorX ? anchoredX : centeredX,
              viewportRect.width,
              scaledDimensions.width,
              newOverflow.width,
            );
        const targetY = shouldRecenter
          ? centeredY
          : getAxisPosition(
              shouldAnchorY ? anchoredY : centeredY,
              viewportRect.height,
              scaledDimensions.height,
              newOverflow.height,
            );

        setIsOverflowing(newOverflow.width || newOverflow.height);
        isFitInitializedRef.current = true;
        hasPendingFitRef.current = false;
        hasUserInteractedRef.current = true;
        transformRef.current.setTransform(targetX, targetY, newScale, 0);
      };

      wheelElement.addEventListener('wheel', handleWheelInterceptor, {
        passive: false,
        capture: true,
      });

      return () => {
        clearScheduledFit();
        resizeObserver.disconnect();
        wheelElement.removeEventListener('wheel', handleWheelInterceptor, true);
      };
    }, [
      clearScheduledFit,
      getBaseDimensions,
      getOverflowState,
      getScaledDimensions,
      getViewportElement,
      scheduleFitTransform,
      setMinimumScale,
    ]);

    return (
      <div ref={wheelAreaRef} className="h-full w-full">
        <TransformWrapper
          key={imagePath}
          ref={transformRef}
          initialScale={minScale}
          minScale={minScale}
          maxScale={MAX_SCALE}
          centerOnInit
          limitToBounds={!isOverflowing}
          centerZoomedOut={true}
          wheel={{
            disabled: true,
          }}
          panning={{
            disabled: !isOverflowing,
            velocityDisabled: true,
          }}
          onTransformed={(ref) => {
            const scale = ref.state.scale;
            const wrapper = getViewportElement();
            if (!wrapper) return;

            const rect = wrapper.getBoundingClientRect();
            const overflow = getOverflowState(scale, rect.width, rect.height);
            setIsOverflowing(overflow.width || overflow.height);
          }}
          onZoom={(ref) => {
            const scale = ref.state.scale;
            const wrapper = getViewportElement();
            if (!wrapper) return;

            const rect = wrapper.getBoundingClientRect();
            const overflow = getOverflowState(scale, rect.width, rect.height);
            setIsOverflowing(overflow.width || overflow.height);
          }}
          onPanning={(ref) => {
            hasUserInteractedRef.current = true;
            const scale = ref.state.scale;
            const wrapper = getViewportElement();
            if (!wrapper || !imageRef.current) return;

            const rect = wrapper.getBoundingClientRect();
            const overflow = getOverflowState(scale, rect.width, rect.height);
            setIsOverflowing(overflow.width || overflow.height);

            const positionX = ref.state.positionX;
            const positionY = ref.state.positionY;
            const viewW = wrapper.clientWidth;
            const viewH = wrapper.clientHeight;
            const baseDimensions = getBaseDimensions();

            if (!baseDimensions) return;

            const scaledW = baseDimensions.width * scale;
            const scaledH = baseDimensions.height * scale;

            const finalX = getAxisPosition(
              positionX,
              viewW,
              scaledW,
              overflow.width,
            );
            const finalY = getAxisPosition(
              positionY,
              viewH,
              scaledH,
              overflow.height,
            );
            const clamped = positionX !== finalX || positionY !== finalY;

            if (clamped) {
              ref.setTransform(finalX, finalY, scale, 0);
            }
          }}
        >
          <TransformComponent
            wrapperStyle={{
              width: '100%',
              height: '100%',
              overflow: 'visible',
              cursor: isOverflowing ? 'move' : 'default',
            }}
            contentStyle={{
              width: 'fit-content',
              height: 'fit-content',
              cursor: isOverflowing ? 'move' : 'default',
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
                maxWidth: 'none',
                maxHeight: 'none',
                objectFit: 'contain',
                zIndex: 50,
                transform: `rotate(${rotation}deg)`,
                cursor: isOverflowing ? 'move' : 'default',
              }}
            />
          </TransformComponent>
        </TransformWrapper>
      </div>
    );
  },
);

ZoomableImage.displayName = 'ZoomableImage';
