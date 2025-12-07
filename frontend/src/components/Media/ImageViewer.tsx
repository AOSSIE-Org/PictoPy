import React, { useRef, useImperativeHandle, forwardRef, useState, useEffect } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { convertFileSrc } from '@tauri-apps/api/core';

interface ImageViewerProps {
  imagePath: string;
  alt: string;
  rotation: number;
  resetSignal?: number;
}

export interface ImageViewerRef {
  zoomIn: () => void;
  zoomOut: () => void;
  reset: () => void;
}

export const ImageViewer = forwardRef<ImageViewerRef, ImageViewerProps>(
  ({ imagePath, alt, rotation, resetSignal }, ref) => {
    const transformRef = useRef<any>(null);
    const containerRef = useRef<HTMLDivElement | null>(null);
    const imgRef = useRef<HTMLImageElement | null>(null);
    const [minScale, setMinScale] = useState<number>(0.1);
    const [initialScale, setInitialScale] = useState<number>(1);
    const maxScale = 8;

    // Tuning constants (can be adjusted for feel)
    const ZOOM_EXP_FACTOR = 0.0012; // exponential multiplier sensitivity
    const MIN_MULTIPLIER = 0.75; // clamp of multiplier
    const MAX_MULTIPLIER = 1.45; // clamp of multiplier
    const ZOOM_ANIM_DURATION = 160; // ms for normal zoom
    const SNAP_MIN_DURATION = 300; // ms when snapping to min

    // Expose zoom functions to parent
    useImperativeHandle(ref, () => ({
      zoomIn: () => transformRef.current?.zoomIn(),
      zoomOut: () => transformRef.current?.zoomOut(),
      reset: () => transformRef.current?.resetTransform(),
    }));

    // Reset on signal change
    React.useEffect(() => {
      transformRef.current?.resetTransform();
    }, [resetSignal]);

    // Compute dynamic min scale (fit to screen) whenever image or container size changes
    const computeMinScale = () => {
      const img = imgRef.current;
      const container = containerRef.current;
      if (!img || !container) return;
      const naturalW = img.naturalWidth || img.width;
      const naturalH = img.naturalHeight || img.height;
      const { width: contW, height: contH } = container.getBoundingClientRect();
      if (!naturalW || !naturalH || !contW || !contH) return;
      const scale = Math.min(contW / naturalW, contH / naturalH, 1);
      setMinScale(scale);
      setInitialScale(scale);
      // if transform already initialized, ensure we don't go below new min
      try {
        const anyRef = transformRef.current as any;
        const current = anyRef?.state?.scale ?? anyRef?.transformComponent?.state?.scale ?? null;
        if (current !== null && current < scale) {
          anyRef?.setTransform?.(scale, 0, 0);
        }
      } catch (e) {
        // no-op
      }
    };

    useEffect(() => {
      // recompute when image loads and on resize
      const img = imgRef.current;
      if (img && img.complete) {
        computeMinScale();
      }
      const handleResize = () => computeMinScale();
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }, []);

    // handle wheel (zoom) with axis-dependent anchoring
    const onWheel = (e: React.WheelEvent) => {
      if (!transformRef.current) return;
      e.preventDefault();
      const anyRef = transformRef.current as any;
      const state = anyRef?.state ?? anyRef?.transformComponent?.state ?? {};
      const prevScale: number = state?.scale ?? initialScale ?? 1;

      const delta = -e.deltaY;
      // adaptive zoom multiplier: map wheel delta to an exponential multiplier for smooth control
      const rawMultiplier = Math.exp(delta * ZOOM_EXP_FACTOR);
      const zoomFactor = Math.max(MIN_MULTIPLIER, Math.min(MAX_MULTIPLIER, rawMultiplier));
      let newScale = prevScale * zoomFactor;
      newScale = Math.max(minScale, Math.min(maxScale, newScale));

      // get container and image metrics
      const container = containerRef.current;
      const img = imgRef.current;
      if (!container || !img) {
        anyRef?.setTransform?.(newScale, 0, 0);
        return;
      }
      const { left: contL, top: contT, width: contW, height: contH } = container.getBoundingClientRect();
      const imgW = img.naturalWidth || img.width;
      const imgH = img.naturalHeight || img.height;

      // displayed sizes at previous and next scale
      const nextDispW = imgW * newScale;
      const nextDispH = imgH * newScale;

      // determine axis overflow
      const overflowX = nextDispW > contW;
      const overflowY = nextDispH > contH;

      // cursor position relative to container
      const cursorX = e.clientX - contL;
      const cursorY = e.clientY - contT;

      // compute new translate so that anchor point stays under cursor when overflowing on that axis
      // basic formula: newPos = (prevPos - anchor) * (newScale/prevScale) + anchor
      // but we don't have prevPos; use transform state if available
      const prevPosX = state?.positionX ?? 0;
      const prevPosY = state?.positionY ?? 0;

      // anchor in content coordinates (relative to centered origin)
      const anchorX = cursorX - contW / 2;
      const anchorY = cursorY - contH / 2;

      let newPosX = 0;
      let newPosY = 0;

      // X axis: center if no overflow, else cursor anchored
      if (!overflowX) {
        newPosX = 0; // center
      } else {
        newPosX = (prevPosX - anchorX) * (newScale / prevScale) + anchorX;
      }

      if (!overflowY) {
        newPosY = 0;
      } else {
        newPosY = (prevPosY - anchorY) * (newScale / prevScale) + anchorY;
      }

      // animation duration: smooth when zooming, slightly longer when snapping to min
      const duration = newScale === minScale ? SNAP_MIN_DURATION : ZOOM_ANIM_DURATION;
      anyRef?.setTransform?.(newScale, newPosX, newPosY, duration);
    };

    return (
      <div ref={containerRef} data-testid="image-viewer-container" style={{ width: '100%', height: '100%' }}>
        <TransformWrapper
          ref={transformRef}
          initialScale={initialScale}
          minScale={minScale}
          maxScale={maxScale}
          centerOnInit
          limitToBounds={false}
          wheel={{ disabled: true }}
        >
          <TransformComponent
            wrapperStyle={{
              width: '100%',
              height: '100%',
              overflow: 'hidden',
            }}
            contentStyle={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <img
              ref={imgRef}
              src={convertFileSrc(imagePath) || '/placeholder.svg'}
              alt={alt}
              draggable={false}
              className="select-none"
              onError={(e) => {
                const img = e.target as HTMLImageElement;
                img.onerror = null;
                img.src = '/placeholder.svg';
              }}
              onLoad={() => computeMinScale()}
              onWheel={(e) => onWheel(e)}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                zIndex: 50,
                transform: `rotate(${rotation}deg)`,
                cursor: 'grab',
              }}
            />
          </TransformComponent>
        </TransformWrapper>
      </div>
    );
  },
);
