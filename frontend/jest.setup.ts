import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';

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
