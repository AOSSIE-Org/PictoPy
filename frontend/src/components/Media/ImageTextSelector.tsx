import React, { useEffect, useRef, useState } from 'react';
import type { OCRResult, OCRBox } from '../../ocr/ocrWorker';
import { runOCR, getCachedOCR, initOCRWorker } from '../../ocr/ocrWorker';
import './ImageTextSelector.css';

type Props = {
  imageUrl: string;
  alt?: string;
  className?: string;
};

export const ImageTextSelector: React.FC<Props> = ({ imageUrl, alt, className }) => {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedBoxes, setSelectedBoxes] = useState<Set<number>>(new Set());
  const [selectionRect, setSelectionRect] = useState<{ x:number;y:number;width:number;height:number } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const startPoint = useRef<{x:number;y:number}|null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key.toLowerCase() === 't') {
        e.preventDefault();
        setSelectionMode((s) => !s);
        if (!selectionMode) {
          // lazy init worker
          initOCRWorker();
        }
      }
      if (e.key === 'Escape') {
        setSelectedBoxes(new Set());
        setSelectionRect(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selectionMode]);

  useEffect(() => {
    if (!selectionMode) return;
    // run OCR lazily
    let mounted = true;
    (async () => {
      try {
        const cached = getCachedOCR(imageUrl);
        if (cached) {
          if (!mounted) return;
          setOcrResult(cached);
          return;
        }
        const res = await runOCR(imageUrl);
        if (!mounted) return;
        setOcrResult(res);
      } catch (e) {
        console.error('OCR error', e);
      }
    })();
    return () => { mounted = false; };
  }, [selectionMode, imageUrl]);

  // map OCR coords to DOM coords using image natural dims + getBoundingClientRect
  const mapBox = (box: OCRBox) => {
    const img = imgRef.current;
    const container = containerRef.current;
    if (!img || !container || !ocrResult) return null;
    const rect = img.getBoundingClientRect();
    const scaleX = rect.width / ocrResult.width;
    const scaleY = rect.height / ocrResult.height;
    return { left: box.x * scaleX, top: box.y * scaleY, width: box.width * scaleX, height: box.height * scaleY };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!selectionMode) return;
    setIsSelecting(true);
    const container = containerRef.current!;
    const r = container.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    startPoint.current = { x, y };
    setSelectionRect({ x, y, width: 0, height: 0 });
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isSelecting || !startPoint.current) return;
    const container = containerRef.current!;
    const r = container.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    const sx = Math.min(startPoint.current.x, x);
    const sy = Math.min(startPoint.current.y, y);
    const w = Math.abs(x - startPoint.current.x);
    const h = Math.abs(y - startPoint.current.y);
    setSelectionRect({ x: sx, y: sy, width: w, height: h });
  };
  const handleMouseUp = () => {
    if (!isSelecting) return;
    setIsSelecting(false);
    startPoint.current = null;
    // compute selected boxes
    if (!selectionRect || !ocrResult) return;
    const boxes = new Set<number>();
    const rect = imgRef.current!.getBoundingClientRect();
    const scaleX = ocrResult.width / rect.width;
    const scaleY = ocrResult.height / rect.height;
    const sel = { x: selectionRect.x * scaleX, y: selectionRect.y * scaleY, width: selectionRect.width * scaleX, height: selectionRect.height * scaleY };
    ocrResult.boxes.forEach((b, idx) => {
      const bx = b.x, by = b.y, bw = b.width, bh = b.height;
      const intersects = !(bx + bw < sel.x || bx > sel.x + sel.width || by + bh < sel.y || by > sel.y + sel.height);
      if (intersects) boxes.add(idx);
    });
    setSelectedBoxes(boxes);
  };

  const copySelection = async (includeMeta = true) => {
    if (!ocrResult) return;
    const texts: string[] = [];
    const boxes: any[] = [];
    Array.from(selectedBoxes).sort((a,b)=>a-b).forEach((i)=>{
      const b = ocrResult.boxes[i];
      if (b) { texts.push(b.text); boxes.push(b); }
    });
    const text = texts.join(' ');
    try {
      if (navigator.clipboard && navigator.clipboard.write) {
        const items: any[] = [];
        items.push(new ClipboardItem({ 'text/plain': new Blob([text], { type:'text/plain' }) }));
        if (includeMeta) {
          const meta = JSON.stringify({ text, boxes, confidence: boxes.map((x:any)=>x.confidence) });
          items.push(new ClipboardItem({ 'application/json': new Blob([meta], { type:'application/json' }) }));
        }
        // @ts-ignore
        await navigator.clipboard.write(items);
      } else {
        // fallback
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
    } catch (e) {
      console.error('Copy failed', e);
    }
  };

  const refineSelection = async () => {
    if (!ocrResult || !selectionRect) return;
    // map selectionRect back to image coords and run OCR for that rect at higher resolution
    const imgRect = imgRef.current!.getBoundingClientRect();
    const sx = Math.round(selectionRect.x * (ocrResult.width / imgRect.width));
    const sy = Math.round(selectionRect.y * (ocrResult.height / imgRect.height));
    const sw = Math.round(selectionRect.width * (ocrResult.width / imgRect.width));
    const sh = Math.round(selectionRect.height * (ocrResult.height / imgRect.height));
    // debounce: small delay
    const res = await runOCR(imageUrl, { rect: { x: sx, y: sy, width: sw, height: sh }, maxWidth: sw, maxHeight: sh });
    // merge boxes: replace intersecting boxes in ocrResult with refined ones
    const newBoxes = [...ocrResult.boxes];
    // remove boxes that intersect selection
    const filtered = newBoxes.filter((b)=>!(b.x < sx+sw && b.x+b.width > sx && b.y < sy+sh && b.y+b.height > sy));
    // adjust refined box coordinates relative to full image
    res.boxes.forEach((b)=>{
      filtered.push({ ...b, x: b.x + sx, y: b.y + sy });
    });
    setOcrResult({ ...ocrResult, boxes: filtered, text: (ocrResult.text + '\n' + res.text).trim() });
  };

  return (
    <div className={`image-text-selector ${className||''}`}>
      <div className="its-image-container" ref={containerRef} onMouseDown={handleMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}>
        <img ref={imgRef} src={imageUrl} alt={alt||''} className="its-image" />
        {selectionMode && ocrResult && (
          <div className="its-overlay" aria-hidden>{ocrResult.boxes.map((b, idx) => {
            const mapped = mapBox(b);
            if (!mapped) return null;
            const selected = selectedBoxes.has(idx);
            return (
              <div key={idx} className={`its-box ${selected? 'selected':''}`} style={{ left: mapped.left, top: mapped.top, width: mapped.width, height: mapped.height }} data-idx={idx} role="button" aria-label={`text-box-${idx}`}>{b.text}</div>
            );
          })}
            {selectionRect && <div className="its-selection-rect" style={{ left: selectionRect.x, top: selectionRect.y, width: selectionRect.width, height: selectionRect.height }} />}
          </div>
        )}
      </div>
      {selectionMode && (
        <div className="its-controls" aria-hidden>
          <button onClick={()=>copySelection(true)} aria-label="Copy selection">Copy</button>
          <button onClick={()=>refineSelection()} aria-label="Refine selection">Refine</button>
        </div>
      )}
    </div>
  );
};

export default ImageTextSelector;
