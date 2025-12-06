import { useRef, useImperativeHandle, forwardRef, useState, useEffect } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { convertFileSrc } from '@tauri-apps/api/core';
import { ocrService } from '../../services/OCRService';
import { TextOverlay } from './TextOverlay';
import { Page } from 'tesseract.js';
import { Loader2, ScanText } from 'lucide-react';

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
    const imgRef = useRef<HTMLImageElement>(null);
    const [isOCRActive, setIsOCRActive] = useState(false);
    const [ocrData, setOcrData] = useState<Page | null>(null);
    const [isOCRLoading, setIsOCRLoading] = useState(false);
    const [imageScale, setImageScale] = useState(1);

    // Expose zoom functions to parent
    useImperativeHandle(ref, () => ({
      zoomIn: () => transformRef.current?.zoomIn(),
      zoomOut: () => transformRef.current?.zoomOut(),
      reset: () => transformRef.current?.resetTransform(),
    }));

    // Reset on signal change
    useEffect(() => {
      transformRef.current?.resetTransform();
      // Reset OCR when image changes
      setIsOCRActive(false);
      setOcrData(null);
      setIsOCRLoading(false);
    }, [resetSignal, imagePath]);

    // Update scale when image loads or resizes
    useEffect(() => {
      const updateScale = () => {
        if (imgRef.current) {
          const { width, naturalWidth } = imgRef.current;
          if (naturalWidth > 0) {
            setImageScale(width / naturalWidth);
          }
        }
      };

      const img = imgRef.current;
      if (img) {
        // Initial update
        if (img.complete) updateScale();

        // Listen for load
        img.addEventListener('load', updateScale);

        // Listen for resize
        const resizeObserver = new ResizeObserver(updateScale);
        resizeObserver.observe(img);

        return () => {
          img.removeEventListener('load', updateScale);
          resizeObserver.disconnect();
        };
      }
    }, [imagePath]); // Re-run when image path changes

    // Handle Ctrl+T to toggle OCR
    const imagePathRef = useRef(imagePath);
    useEffect(() => {
      imagePathRef.current = imagePath;
    }, [imagePath]);

    useEffect(() => {
      const handleKeyDown = async (e: KeyboardEvent) => {
        if (e.ctrlKey && e.key.toLowerCase() === 't') {
          e.preventDefault();

          if (isOCRActive) {
            // Deactivate
            setIsOCRActive(false);
          } else {
            // Activate
            setIsOCRActive(true);
            if (!ocrData && !isOCRLoading) {
              setIsOCRLoading(true);
              try {
                const src = convertFileSrc(imagePath);
                const data = await ocrService.recognize(src);
                // Only set data if image hasn't changed
                if (imagePath === imagePathRef.current) {
                  setOcrData(data);
                }
              } catch (error) {
                console.error('Failed to perform OCR', error);
                setIsOCRActive(false); // Revert if failed
              } finally {
                if (imagePath === imagePathRef.current) {
                  setIsOCRLoading(false);
                }
              }
            }
          }
        }
      };

      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }, [imagePath, isOCRActive, ocrData, isOCRLoading]);

    return (
      <div className="relative w-full h-full">
        {/* Text Detection Toggle Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (isOCRActive) {
              setIsOCRActive(false);
            } else {
              setIsOCRActive(true);
              if (!ocrData && !isOCRLoading) {
                // Trigger loading logic same as Ctrl+T
                // We need to extract the loading logic into a reusable function or trigger it via effect if isOCRActive changes to true?
                // The effect at line 118 depends on isOCRActive, but the keydown handler (line 84) sets state AND triggers logic.
                // Let's refactor slightly to share logic or just duplicate the trigger here safely.
                // Actually, the keydown handler does the heavy lifting.
                // It's cleaner to just set the state and let an effect handle it, OR duplicate the call.
                // Given the existing structure, I'll duplicate the trigger logic for now to ensure immediate feedback.
                setIsOCRLoading(true);
                (async () => {
                  try {
                    const src = convertFileSrc(imagePath);
                    const data = await ocrService.recognize(src);
                    if (imagePath === imagePathRef.current) {
                      setOcrData(data);
                    }
                  } catch (error) {
                    console.error('Failed to perform OCR', error);
                    setIsOCRActive(false);
                  } finally {
                    if (imagePath === imagePathRef.current) {
                      setIsOCRLoading(false);
                    }
                  }
                })();
              }
            }
          }}
          className={`absolute top-6 left-6 z-60 flex items-center gap-2 rounded-full border border-white/10 px-4 py-2.5 backdrop-blur-md transition-all duration-300 ${isOCRActive
            ? 'bg-blue-600/90 text-white shadow-[0_0_20px_rgba(37,99,235,0.5)]'
            : 'bg-zinc-900/80 text-white/90 hover:bg-zinc-800/90 hover:shadow-lg'
            }`}
        >
          <ScanText className={`h-4 w-4 ${isOCRActive ? 'animate-pulse' : ''}`} />
          <span className="text-sm font-medium">Text Detection</span>
          <span className="ml-1 hidden rounded bg-white/20 px-1.5 py-0.5 text-[10px] sm:inline-block">
            Ctrl + T
          </span>
        </button>

        {isOCRLoading && (
          <div className="absolute top-20 left-6 z-60 bg-zinc-900/80 text-white px-4 py-2 rounded-full flex items-center gap-3 backdrop-blur-md border border-white/10 shadow-xl animate-in fade-in slide-in-from-top-2 duration-300">
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            <span className="text-sm font-medium tracking-wide">Processing Text...</span>
          </div>
        )}

        {isOCRActive && !isOCRLoading && ocrData && (
          <div className="absolute top-20 left-6 z-60 bg-blue-600/90 text-white px-4 py-2 rounded-full flex items-center gap-2 backdrop-blur-md border border-white/10 shadow-xl animate-in fade-in slide-in-from-top-2 duration-300">
            <span className="relative flex h-2.5 w-2.5 mr-1">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white"></span>
            </span>
            <span className="text-sm font-medium tracking-wide">Text Selection Active</span>
          </div>
        )}

        <TransformWrapper
          ref={transformRef}
          initialScale={1}
          minScale={0.1}
          maxScale={8}
          centerOnInit
          limitToBounds={false}
          panning={{ disabled: isOCRActive }}
        >
          <TransformComponent
            wrapperStyle={{
              width: '100%',
              height: '100%',
              overflow: 'visible',
            }}
            contentStyle={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                position: 'relative',
                transform: `rotate(${rotation}deg)`,
                maxWidth: '100%',
                maxHeight: '100%',
              }}
            >
              <img
                ref={imgRef}
                src={convertFileSrc(imagePath) || '/placeholder.svg'}
                alt={alt}
                draggable={false}
                className="select-none block max-w-full max-h-full"
                onError={(e) => {
                  const img = e.target as HTMLImageElement;
                  img.onerror = null;
                  img.src = '/placeholder.svg';
                }}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: 'contain',
                  zIndex: 50,
                }}
              />
              {isOCRActive && ocrData && (
                <TextOverlay ocrData={ocrData} scale={imageScale} />
              )}
            </div>
          </TransformComponent>
        </TransformWrapper>
      </div>
    );
  },
);
