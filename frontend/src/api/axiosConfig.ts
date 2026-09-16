import axios from 'axios';
import { BACKEND_URL, SYNC_MICROSERVICE_URL } from '@/config/Backend';

// Default timeout for ordinary requests. Endpoints whose runtime scales with
// library size pass a longer per-call `timeout` override instead.
const DEFAULT_TIMEOUT_MS = 30000;

// Endpoints that scan the full library (face search, multi-person search)
// should pass `{ timeout: LONG_REQUEST_TIMEOUT_MS }` per call instead.
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
