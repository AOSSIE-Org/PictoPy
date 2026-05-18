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
const PAN_PADDING = 20;

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

export const ZoomableImage = forwardRef<ZoomableImageRef, ZoomableImageProps>(
  ({ imagePath, alt, rotation, resetSignal }, ref) => {
    const transformRef = useRef<ReactZoomPanPinchRef>(null);
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

    const getOverflowState = useCallback(
      (scale: number, viewportWidth: number, viewportHeight: number) => {
        if (!imageRef.current) return { width: false, height: false };

        const imgElement = imageRef.current;
        const renderedWidth = imgElement.clientWidth;
        const renderedHeight = imgElement.clientHeight;

        const effectiveDims = getEffectiveDimensions(
          renderedWidth,
          renderedHeight,
        );
        const scaledWidth = effectiveDims.width * scale;
        const scaledHeight = effectiveDims.height * scale;

        return {
          width: scaledWidth > viewportWidth,
          height: scaledHeight > viewportHeight,
        };
      },
      [getEffectiveDimensions],
    );

    const handleReset = useCallback(
      (duration = 200, animationType: AnimationType = 'easeOut') => {
        if (
          !transformRef.current?.instance?.wrapperComponent ||
          !imageRef.current
        )
          return;

        const wrapperRect =
          transformRef.current.instance.wrapperComponent.getBoundingClientRect();
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

        const centerX = (wrapperRect.width - renderedW) / 2;
        const centerY = (wrapperRect.height - renderedH) / 2;

        transformRef.current.setTransform(
          centerX,
          centerY,
          scale,
          duration,
          animationType,
        );
        setIsOverflowing(false);
      },
      [getEffectiveDimensions],
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
      if (
        !transformRef.current?.instance?.wrapperComponent ||
        !imageRef.current
      )
        return;

      const wrapper = transformRef.current.instance.wrapperComponent;
      const scale = transformRef.current.instance.transformState.scale;
      const rect = wrapper.getBoundingClientRect();

      const overflow = getOverflowState(scale, rect.width, rect.height);
      setIsOverflowing(overflow.width || overflow.height);
    }, [rotation, getOverflowState]);

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
      const wrapperElement = transformRef.current?.instance?.wrapperComponent;
      if (!wrapperElement) return;

      let cachedWrapperRect = wrapperElement.getBoundingClientRect();

      const resizeObserver = new ResizeObserver(() => {
        cachedWrapperRect = wrapperElement.getBoundingClientRect();
      });

      resizeObserver.observe(wrapperElement);

      const handleWheelInterceptor = (e: WheelEvent) => {
        if (!imageRef.current || !transformRef.current) return;

        const transformState = transformRef.current.instance.transformState;

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

        const wrapperRect = cachedWrapperRect;
        const newOverflow = getOverflowState(
          newScale,
          wrapperRect.width,
          wrapperRect.height,
        );

        if (zoomChange < 0) {
          e.preventDefault();
          e.stopPropagation();

          setIsOverflowing(newOverflow.width || newOverflow.height);

          const baseW = imageRect.width / currentScale;
          const baseH = imageRect.height / currentScale;

          const effectiveDims = getEffectiveDimensions(baseW, baseH);
          const finalTargetX = (wrapperRect.width - effectiveDims.width) / 2;
          const finalTargetY = (wrapperRect.height - effectiveDims.height) / 2;

          let targetX = finalTargetX;
          let targetY = finalTargetY;

          if (currentScale > 1) {
            const ratio = (newScale - 1) / (currentScale - 1);
            const safeRatio =
              isNaN(ratio) || !isFinite(ratio) || ratio < 0 ? 0 : ratio;

            targetX =
              transformState.positionX * safeRatio +
              finalTargetX * (1 - safeRatio);
            targetY =
              transformState.positionY * safeRatio +
              finalTargetY * (1 - safeRatio);
          }

          transformRef.current.setTransform(targetX, targetY, newScale, 0);
          return;
        }

        if (!newOverflow.width && !newOverflow.height) {
          e.preventDefault();
          e.stopPropagation();

          const baseW = imageRect.width / currentScale;
          const baseH = imageRect.height / currentScale;

          const effectiveDims = getEffectiveDimensions(baseW, baseH);
          const nextW = effectiveDims.width * newScale;
          const nextH = effectiveDims.height * newScale;

          const targetX = (wrapperRect.width - nextW) / 2;
          const targetY = (wrapperRect.height - nextH) / 2;

          transformRef.current.setTransform(targetX, targetY, newScale, 0);
          return;
        }

        if (!isOverImage) {
          e.preventDefault();
          e.stopPropagation();

          const centerX = wrapperRect.width / 2;
          const centerY = wrapperRect.height / 2;

          if (currentScale > 0) {
            const ratio = newScale / currentScale;

            const targetX =
              centerX - (centerX - transformState.positionX) * ratio;
            const targetY =
              centerY - (centerY - transformState.positionY) * ratio;

            transformRef.current.setTransform(targetX, targetY, newScale, 0);
          }
          return;
        }
      };

      wrapperElement.addEventListener('wheel', handleWheelInterceptor, {
        passive: false,
        capture: true,
      });

      return () => {
        resizeObserver.disconnect();
        wrapperElement.removeEventListener(
          'wheel',
          handleWheelInterceptor,
          true,
        );
      };
    }, [getEffectiveDimensions, getOverflowState]);

    return (
      <TransformWrapper
        ref={transformRef}
        initialScale={MIN_SCALE}
        minScale={MIN_SCALE}
        maxScale={MAX_SCALE}
        centerOnInit
        limitToBounds={!isOverflowing}
        centerZoomedOut={true}
        wheel={{
          disabled: false,
          step: 0.1,
          smoothStep: 0.001,
        }}
        panning={{
          disabled: !isOverflowing,
          velocityDisabled: true,
        }}
        onTransformed={(ref) => {
          const scale = ref.state.scale;
          const wrapper = ref.instance.wrapperComponent;
          if (!wrapper) return;

          const rect = wrapper.getBoundingClientRect();
          const overflow = getOverflowState(scale, rect.width, rect.height);
          setIsOverflowing(overflow.width || overflow.height);
        }}
        onZoom={(ref) => {
          const scale = ref.state.scale;
          const wrapper = ref.instance.wrapperComponent;
          if (!wrapper) return;

          const rect = wrapper.getBoundingClientRect();
          const overflow = getOverflowState(scale, rect.width, rect.height);
          setIsOverflowing(overflow.width || overflow.height);
        }}
        onPanning={(ref) => {
          const scale = ref.state.scale;
          const wrapper = ref.instance.wrapperComponent;
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

          const limitLeft = -scaledW + PAN_PADDING;
          const limitRight = viewW - PAN_PADDING;
          const limitTop = -scaledH + PAN_PADDING;
          const limitBottom = viewH - PAN_PADDING;

          let finalX = positionX;
          let finalY = positionY;
          let clamped = false;

          if (positionX < limitLeft) {
            finalX = limitLeft;
            clamped = true;
          } else if (positionX > limitRight) {
            finalX = limitRight;
            clamped = true;
          }

          if (positionY < limitTop) {
            finalY = limitTop;
            clamped = true;
          } else if (positionY > limitBottom) {
            finalY = limitBottom;
            clamped = true;
          }

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
    );
  },
);

ZoomableImage.displayName = 'ZoomableImage';
