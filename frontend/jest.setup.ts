import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';

// Suppress console.log during tests
const originalConsoleLog = console.log;
beforeAll(() => {
  console.log = jest.fn();
});
afterAll(() => {
  console.log = originalConsoleLog;
});

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

// --- Tauri Mocks ---

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock Tauri Internals
(window as any).__TAURI_INTERNALS__ = {
  invoke: jest.fn().mockResolvedValue(null),
  transformCallback: jest.fn(),
  metadata: {},
};

// Mock the module imports
jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
}));

jest.mock('@tauri-apps/api/app', () => ({
  getVersion: jest.fn().mockResolvedValue('1.0.0'),
  getName: jest.fn().mockResolvedValue('PictoPy'),
  getTauriVersion: jest.fn().mockResolvedValue('2.0.0'),
}));

jest.mock('@tauri-apps/plugin-updater', () => ({
  check: jest.fn().mockResolvedValue(null),
}));

jest.mock('@tauri-apps/plugin-dialog', () => ({
  save: jest.fn().mockResolvedValue(null),
  open: jest.fn().mockResolvedValue(null),
  ask: jest.fn().mockResolvedValue(false),
}));

jest.mock('@tauri-apps/plugin-fs', () => ({
  readDir: jest.fn().mockResolvedValue([]),
  createDir: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('@tauri-apps/plugin-shell', () => ({
  open: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('@tauri-apps/plugin-store', () => ({
  Store: jest.fn().mockImplementation(() => ({
    get: jest.fn().mockResolvedValue(null),
    set: jest.fn().mockResolvedValue(undefined),
    save: jest.fn().mockResolvedValue(undefined),
    load: jest.fn().mockResolvedValue(undefined),
    delete: jest.fn().mockResolvedValue(true),
    has: jest.fn().mockResolvedValue(false),
    clear: jest.fn().mockResolvedValue(undefined),
    keys: jest.fn().mockResolvedValue([]),
    values: jest.fn().mockResolvedValue([]),
    entries: jest.fn().mockResolvedValue([]),
    length: jest.fn().mockResolvedValue(0),
    onKeyChange: jest.fn().mockResolvedValue(() => {}), // Returns unlisten function
    onChange: jest.fn().mockResolvedValue(() => {}), // Returns unlisten function
  })),
}));

// Mock Axios
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn().mockResolvedValue({ data: [] }),
    post: jest.fn().mockResolvedValue({ data: {} }),
    put: jest.fn().mockResolvedValue({ data: {} }),
    patch: jest.fn().mockResolvedValue({ data: {} }),
    delete: jest.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
  };
  return {
    default: mockAxiosInstance,
    create: jest.fn(() => mockAxiosInstance),
    ...mockAxiosInstance,
  };
});
