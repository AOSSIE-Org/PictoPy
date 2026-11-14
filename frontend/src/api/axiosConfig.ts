import axios from 'axios';
import { BACKEND_URL, SYNC_MICROSERVICE_URL } from '@/config/Backend';

const DEFAULT_TIMEOUT_MS = 30000;

// Passed per call by endpoints that scan the whole library, like face search.
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
