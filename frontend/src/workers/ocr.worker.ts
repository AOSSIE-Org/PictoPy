// ocr.worker.ts — runs Tesseract.js in a web worker (if available)
// Message protocol: postMessage({type:'ocr', id, payload:{imageUrl, rect, maxWidth, maxHeight}})
// Reply: postMessage({id, type:'ocrResult', payload: OCRResult})

import type { OCRResult } from '../ocr/ocrWorker';

// We'll dynamically import tesseract.js to keep bundle small
let tesseract: any = null;

async function ensureTesseract() {
  if (tesseract) return tesseract;
  try {
    // dynamic import
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const mod = await import('tesseract.js');
    tesseract = mod;
    return tesseract;
  } catch (e) {
    // If import fails (tests), provide a simple mock that returns empty result
    console.warn('tesseract.js not available in worker; OCR will be mocked.', e);
    tesseract = null;
    return null;
  }
}

async function runOCRJob(imageUrl: string, rect?: {x:number;y:number;width:number;height:number}, maxWidth?: number, maxHeight?: number): Promise<OCRResult> {
  const mod = await ensureTesseract();
  if (!mod) {
    // mock: return single box covering full image with alt text blank
    return {
      boxes: [],
      text: '',
      width: maxWidth || 0,
      height: maxHeight || 0,
    };
  }
  // fetch image as blob
  const resp = await fetch(imageUrl);
  const blob = await resp.blob();
  // create an offscreen canvas to crop/resize if rect provided
  let imageBitmap: ImageBitmap | null = null;
  try {
    imageBitmap = await createImageBitmap(blob);
  } catch (e) {
    // fallback
  }

  let canvas: OffscreenCanvas | HTMLCanvasElement | null = null;
  let drawW = imageBitmap ? imageBitmap.width : 0;
  let drawH = imageBitmap ? imageBitmap.height : 0;
  if (rect && imageBitmap) {
    // crop
    drawW = rect.width;
    drawH = rect.height;
    canvas = new OffscreenCanvas(drawW, drawH);
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(imageBitmap, rect.x, rect.y, rect.width, rect.height, 0, 0, drawW, drawH);
  } else if (imageBitmap) {
    canvas = new OffscreenCanvas(drawW, drawH);
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(imageBitmap, 0, 0);
  } else {
    // no imageBitmap: fallback to tesseract on blob directly
    // tesseract can accept blob/url
  }

  const worker = mod.createWorker({
    // logger: m => postMessage({type:'log', payload:m}),
  });
  await worker.load();
  await worker.loadLanguage('eng');
  await worker.initialize('eng');
  // convert canvas to blob/url
  let src: any = imageUrl;
  if (canvas) {
    try {
      const blob2 = await (canvas as OffscreenCanvas).convertToBlob();
      src = URL.createObjectURL(blob2);
    } catch (e) {
      // ignore
    }
  }
  const { data } = await worker.recognize(src);
  // tesseract returns blocks->paragraphs->lines->words with bbox and text
  const boxes: any[] = [];
  if (data && data.words) {
    data.words.forEach((w: any, idx: number) => {
      boxes.push({ x: w.bbox.x0, y: w.bbox.y0, width: w.bbox.x1 - w.bbox.x0, height: w.bbox.y1 - w.bbox.y0, text: w.text, confidence: w.confidence, word: idx });
    });
  }
  const result: OCRResult = { boxes, text: data?.text || '', width: drawW, height: drawH };
  await worker.terminate();
  return result;
}

self.onmessage = async (ev: MessageEvent) => {
  const { type, id, payload } = ev.data || {};
  if (type === 'ocr') {
    const { imageUrl, rect, maxWidth, maxHeight } = payload || {};
    try {
      const res = await runOCRJob(imageUrl, rect, maxWidth, maxHeight);
      (self as any).postMessage({ id, type: 'ocrResult', payload: res });
    } catch (e) {
      (self as any).postMessage({ id, type: 'ocrResult', payload: { error: String(e) } });
    }
  }
};

// For the in-thread shim, allow module to accept a setter
export function setMainThreadPost(fn: any) {
  // store the provided callback on the global so the main thread shim can call it
  try {
    (globalThis as any).__mainPost = fn;
  } catch (e) {
    // ignore
  }
}
