// ocrWorker.ts — abstraction over OCR engine (client-side tesseract.js worker or server API)
// Exposes a simple API: init(), runOCR(imageUrl, rect?), getCached(imageKey), clearCache()

export type OCRBox = {
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
  confidence: number; // 0-100
  line?: number;
  word?: number;
};

export type OCRResult = {
  boxes: OCRBox[];
  text: string;
  width: number;
  height: number;
};

// A very small cache keyed by image url + dims
const cache = new Map<string, OCRResult>();

function makeKey(url: string, w?: number, h?: number) {
  return `${url}::${w || 0}x${h || 0}`;
}

// Minimal interface to a worker. We will spawn a worker that implements the heavy lifting.
let worker: Worker | null = null;
let nextId = 1;
const pending = new Map<number, (res: any) => void>();

export async function initOCRWorker() {
  if (worker) return worker;
  // worker file uses Vite/webpack worker import when built; fallback to dynamic import of a module that uses tesseract.js directly
  try {
    // create worker using new Worker — worker file placed at ../workers/ocr.worker.ts
    // Vite: new URL import is supported; to keep this file simple we instantiate the worker by relative path
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    worker = new Worker(new URL('../workers/ocr.worker.ts', import.meta.url), { type: 'module' });
    worker.onmessage = (ev) => {
      const { id, payload } = ev.data || {};
      if (id && pending.has(id)) {
        const cb = pending.get(id)!;
        pending.delete(id);
        cb(payload);
      }
    };
    return worker;
  } catch (e) {
    console.warn('Could not spawn OCR worker; falling back to in-thread OCR (may block UI).', e);
    // Try dynamic import of worker module and use a fake worker shim
    const module = await import('../workers/ocr.worker');
    // create a shim that calls module.onmessage
    worker = {
      postMessage(msg: any) {
        // module handles messages via exported function
        // @ts-ignore
        module.onmessage({ data: msg, __fake: true });
      },
      onmessage: null as any,
      terminate() {},
    } as unknown as Worker;
    // @ts-ignore
    module.setMainThreadPost((data: any) => {
      if (worker && (worker as any).onmessage) (worker as any).onmessage({ data });
    });
    return worker;
  }
}

export async function runOCR(imageUrl: string, opts?: { rect?: { x:number;y:number;width:number;height:number}; maxWidth?: number; maxHeight?: number }): Promise<OCRResult> {
  const { rect, maxWidth, maxHeight } = opts || {};
  const key = makeKey(imageUrl, rect?.width || maxWidth, rect?.height || maxHeight);
  if (cache.has(key)) return cache.get(key)!;
  const w = await initOCRWorker();
  return await new Promise<OCRResult>((resolve, reject) => {
    const id = nextId++;
    pending.set(id, (payload: any) => {
      if (payload?.error) return reject(new Error(payload.error));
      const result: OCRResult = payload as OCRResult;
      cache.set(key, result);
      resolve(result);
    });
    w!.postMessage({ type: 'ocr', id, payload: { imageUrl, rect, maxWidth, maxHeight } });
  });
}

export function getCachedOCR(imageUrl: string, w?: number, h?: number) {
  const key = makeKey(imageUrl, w, h);
  return cache.get(key) || null;
}

export function clearCache() {
  cache.clear();
}
