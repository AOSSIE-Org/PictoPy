import {
  useRef,
  useImperativeHandle,
  forwardRef,
  useEffect,
  useState,
} from 'react';
import {
  TransformWrapper,
  TransformComponent,
  ReactZoomPanPinchRef,
} from 'react-zoom-pan-pinch';
import { convertFileSrc } from '@tauri-apps/api/core';

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

    const handleReset = () => {
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

      const imgAspect = baseW / baseH;
      const viewAspect = wrapperRect.width / wrapperRect.height;

      let renderedW, renderedH;
      if (imgAspect > viewAspect) {
        renderedW = Math.min(baseW, wrapperRect.width);
        renderedH = renderedW / imgAspect;
      } else {
        renderedH = Math.min(baseH, wrapperRect.height);
        renderedW = renderedH * imgAspect;
      }

      const centerX = (wrapperRect.width - renderedW) / 2;
      const centerY = (wrapperRect.height - renderedH) / 2;

      transformRef.current.setTransform(
        centerX,
        centerY,
        scale,
        200,
        'easeOut',
      );
      setIsOverflowing(false);
    };

    useImperativeHandle(ref, () => ({
      zoomIn: () => transformRef.current?.zoomIn(),
      zoomOut: () => transformRef.current?.zoomOut(),
      reset: () => handleReset(),
    }));

    useEffect(() => {
      handleReset();
    }, [resetSignal]);
    useEffect(() => {
      setIsOverflowing(false);

      const img = imageRef.current;
      if (!img) return;

      const handleImageLoad = () => {
        if (!transformRef.current?.instance?.wrapperComponent) return;

        const wrapperRect =
          transformRef.current.instance.wrapperComponent.getBoundingClientRect();

        const scale = 1;
        const baseW = img.naturalWidth;
        const baseH = img.naturalHeight;

        const imgAspect = baseW / baseH;
        const viewAspect = wrapperRect.width / wrapperRect.height;

        let renderedW, renderedH;
        if (imgAspect > viewAspect) {
          renderedW = Math.min(baseW, wrapperRect.width);
          renderedH = renderedW / imgAspect;
        } else {
          renderedH = Math.min(baseH, wrapperRect.height);
          renderedW = renderedH * imgAspect;
        }

        const centerX = (wrapperRect.width - renderedW) / 2;
        const centerY = (wrapperRect.height - renderedH) / 2;

        transformRef.current.setTransform(centerX, centerY, scale, 0);
      };

      if (img.complete && img.naturalWidth > 0) {
        handleImageLoad();
      } else {
        img.addEventListener('load', handleImageLoad);
        return () => img.removeEventListener('load', handleImageLoad);
      }
    }, [imagePath]);

    const getOverflowState = (
      scale: number,
      viewportWidth: number,
      viewportHeight: number,
    ) => {
      if (!imageRef.current) return { width: false, height: false };

      const imgElement = imageRef.current;
      const renderedWidth = imgElement.clientWidth;
      const renderedHeight = imgElement.clientHeight;

      const scaledWidth = renderedWidth * scale;
      const scaledHeight = renderedHeight * scale;

      return {
        width: scaledWidth > viewportWidth,
        height: scaledHeight > viewportHeight,
      };
    };

    useEffect(() => {
      const wrapperElement = transformRef.current?.instance?.wrapperComponent;
      if (!wrapperElement) return;

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

        const zoomSpeed = 0.1;
        const delta = e.deltaY > 0 ? -1 : 1;

        const currentScale = transformState.scale;
        const newScale = Math.max(
          1,
          Math.min(8, currentScale + delta * zoomSpeed),
        );

        const wrapperRect = wrapperElement.getBoundingClientRect();
        const newOverflow = getOverflowState(
          newScale,
          wrapperRect.width,
          wrapperRect.height,
        );

        setIsOverflowing(newOverflow.width || newOverflow.height);

        if (delta < 0) {
          e.preventDefault();
          e.stopPropagation();

          const renderedW = imageRect.width / currentScale;
          const renderedH = imageRect.height / currentScale;

          const finalTargetX = (wrapperRect.width - renderedW) / 2;
          const finalTargetY = (wrapperRect.height - renderedH) / 2;

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

        if (!isOverImage || (!newOverflow.width && !newOverflow.height)) {
          e.preventDefault();
          e.stopPropagation();

          const renderedW = imageRect.width;
          const renderedH = imageRect.height;
          const baseW = renderedW / currentScale;
          const baseH = renderedH / currentScale;

          const nextW = baseW * newScale;
          const nextH = baseH * newScale;

          const targetX = (wrapperRect.width - nextW) / 2;
          const targetY = (wrapperRect.height - nextH) / 2;

          transformRef.current.setTransform(targetX, targetY, newScale, 0);
          return;
        }
      };

      wrapperElement.addEventListener('wheel', handleWheelInterceptor, {
        passive: false,
        capture: true,
      });

      return () => {
        wrapperElement.removeEventListener(
          'wheel',
          handleWheelInterceptor,
          true,
        );
      };
    }, []);

    return (
      <TransformWrapper
        ref={transformRef}
        initialScale={1}
        minScale={1}
        maxScale={8}
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

          const scaledW = imgW * scale;
          const scaledH = imgH * scale;

          const limitLeft = -scaledW + 20;
          const limitRight = viewW - 20;
          const limitTop = -scaledH + 20;
          const limitBottom = viewH - 20;

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
