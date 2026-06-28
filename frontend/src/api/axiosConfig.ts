import axios from 'axios';
import { BACKEND_URL, SYNC_MICROSERVICE_URL } from '@/config/Backend';

// Default timeout for ordinary requests. Endpoints whose runtime scales with
// library size pass a longer per-call `timeout` override instead of relying
// on this default.
const DEFAULT_TIMEOUT_MS = 30000;

// For endpoints that run a full scan over the library (face search,
// multi-person search), pass `{ timeout: LONG_REQUEST_TIMEOUT_MS }` per call
// instead of relying on the default above.
export const LONG_REQUEST_TIMEOUT_MS = 120000;

// Create simple axios instance with basic configuration
export const apiClient = axios.create({
  baseURL: BACKEND_URL,
  timeout: DEFAULT_TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
export const syncApiClient = axios.create({
  baseURL: SYNC_MICROSERVICE_URL,
  timeout: DEFAULT_TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
