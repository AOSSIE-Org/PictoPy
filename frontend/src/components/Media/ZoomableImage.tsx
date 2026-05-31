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

type Size = {
  width: number;
  height: number;
};

type OverflowState = {
  width: boolean;
  height: boolean;
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

export const ZoomableImage = forwardRef<ZoomableImageRef, ZoomableImageProps>(
  ({ imagePath, alt, rotation, resetSignal }, ref) => {
    const transformRef = useRef<ReactZoomPanPinchRef>(null);
    const wheelAreaRef = useRef<HTMLDivElement>(null);
    const imageRef = useRef<HTMLImageElement>(null);
    const [isOverflowing, setIsOverflowing] = useState(false);
    const rotationRef = useRef(rotation);

    useEffect(() => {
      rotationRef.current = rotation;
    }, [rotation]);

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

    const getScaledDimensions = useCallback(
      (scale: number): Size | null => {
        if (!imageRef.current) return null;

        const renderedWidth = imageRef.current.clientWidth;
        const renderedHeight = imageRef.current.clientHeight;

        if (!renderedWidth || !renderedHeight) return null;

        const effectiveDims = getEffectiveDimensions(
          renderedWidth,
          renderedHeight,
        );

        return {
          width: effectiveDims.width * scale,
          height: effectiveDims.height * scale,
        };
      },
      [getEffectiveDimensions],
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

    const handleReset = useCallback(
      (duration = 200, animationType: AnimationType = 'easeOut') => {
        const viewportElement = getViewportElement();
        if (!transformRef.current || !viewportElement || !imageRef.current)
          return;

        const wrapperRect = viewportElement.getBoundingClientRect();
        const img = imageRef.current;

        const scale = 1;
        const baseW = img.naturalWidth || img.clientWidth;
        const baseH = img.naturalHeight || img.clientHeight;

        if (!baseW || !baseH) return;

        const effectiveDims = getEffectiveDimensions(baseW, baseH);
        const imgAspect = effectiveDims.width / effectiveDims.height;
        const viewAspect = wrapperRect.width / wrapperRect.height;

        let renderedW, renderedH;
        if (imgAspect > viewAspect) {
          renderedW = Math.min(effectiveDims.width, wrapperRect.width);
          renderedH = renderedW / imgAspect;
        } else {
          renderedH = Math.min(effectiveDims.height, wrapperRect.height);
          renderedW = renderedH * imgAspect;
        }

        const centerX = getCenteredAxisPosition(wrapperRect.width, renderedW);
        const centerY = getCenteredAxisPosition(wrapperRect.height, renderedH);

        transformRef.current.setTransform(
          centerX,
          centerY,
          scale,
          duration,
          animationType,
        );
        setIsOverflowing(false);
      },
      [getEffectiveDimensions, getViewportElement],
    );

    useImperativeHandle(ref, () => ({
      zoomIn: () => transformRef.current?.zoomIn(),
      zoomOut: () => transformRef.current?.zoomOut(),
      reset: () => handleReset(),
    }));

    useEffect(() => {
      handleReset();
    }, [resetSignal, handleReset]);

    useEffect(() => {
      const viewportElement = getViewportElement();
      if (!transformRef.current || !viewportElement || !imageRef.current)
        return;

      const scale = transformRef.current.instance.transformState.scale;
      const rect = viewportElement.getBoundingClientRect();

      const overflow = getOverflowState(scale, rect.width, rect.height);
      setIsOverflowing(overflow.width || overflow.height);
    }, [rotation, getOverflowState, getViewportElement]);

    useEffect(() => {
      setIsOverflowing(false);

      const img = imageRef.current;
      if (!img) return;

      const handleImageLoad = () => {
        handleReset(0);
      };

      if (img.complete && img.naturalWidth > 0) {
        handleImageLoad();
      } else {
        img.addEventListener('load', handleImageLoad);
        return () => img.removeEventListener('load', handleImageLoad);
      }
    }, [imagePath, handleReset]);

    useEffect(() => {
      const wheelElement = wheelAreaRef.current;
      if (!wheelElement) return;

      let cachedViewportRect =
        getViewportElement()?.getBoundingClientRect() ??
        wheelElement.getBoundingClientRect();

      const resizeObserver = new ResizeObserver(() => {
        cachedViewportRect =
          getViewportElement()?.getBoundingClientRect() ??
          wheelElement.getBoundingClientRect();
      });

      resizeObserver.observe(wheelElement);

      const handleWheelInterceptor = (e: WheelEvent) => {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        if (!imageRef.current || !transformRef.current) return;

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

        const currentScale = transformState.scale;
        const newScale = Math.max(
          MIN_SCALE,
          Math.min(MAX_SCALE, currentScale + zoomChange),
        );

        const scaledDimensions = getScaledDimensions(newScale);
        if (!scaledDimensions) return;

        const newOverflow = getOverflowState(
          newScale,
          viewportRect.width,
          viewportRect.height,
        );

        const shouldRecenter =
          newScale === MIN_SCALE || (!newOverflow.width && !newOverflow.height);

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
          mouseViewportX - (mouseViewportX - transformState.positionX) * ratio;
        const anchoredY =
          mouseViewportY - (mouseViewportY - transformState.positionY) * ratio;

        const targetX = shouldRecenter
          ? centeredX
          : getAxisPosition(
              isOverImage ? anchoredX : centeredX,
              viewportRect.width,
              scaledDimensions.width,
              newOverflow.width,
            );
        const targetY = shouldRecenter
          ? centeredY
          : getAxisPosition(
              isOverImage ? anchoredY : centeredY,
              viewportRect.height,
              scaledDimensions.height,
              newOverflow.height,
            );

        setIsOverflowing(newOverflow.width || newOverflow.height);
        transformRef.current.setTransform(targetX, targetY, newScale, 0);
      };

      wheelElement.addEventListener('wheel', handleWheelInterceptor, {
        passive: false,
        capture: true,
      });

      return () => {
        resizeObserver.disconnect();
        wheelElement.removeEventListener('wheel', handleWheelInterceptor, true);
      };
    }, [getOverflowState, getScaledDimensions, getViewportElement]);

    return (
      <div ref={wheelAreaRef} className="h-full w-full">
        <TransformWrapper
          ref={transformRef}
          initialScale={MIN_SCALE}
          minScale={MIN_SCALE}
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
            const imgW = imageRef.current.clientWidth;
            const imgH = imageRef.current.clientHeight;

            const effectiveDims = getEffectiveDimensions(imgW, imgH);
            const scaledW = effectiveDims.width * scale;
            const scaledH = effectiveDims.height * scale;

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
              ref={imageRef}
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
                maxWidth: '100vw',
                maxHeight: '100vh',
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
