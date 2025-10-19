import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';
// REMOVE THESE LINES:
// import { getBackendUrl } from '@/utils/env';
// const backendurl = getBackendUrl()

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}

if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder as unknown as typeof global.TextDecoder;
}

class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

(global as any).ResizeObserver = ResizeObserver;

// Direct value do
Object.defineProperty(global, 'import', {
  value: {
    meta: {
      env: {
        VITE_BACKEND_URL: 'http://localhost:8000'  // Direct value
      }
    }
  }
});