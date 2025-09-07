import axios from 'axios';
import { BACKEND_URL, SYNC_MICROSERVICE_URL } from '@/config/Backend';

// Create simple axios instance with basic configuration
export const apiClient = axios.create({
  baseURL: BACKEND_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
export const syncApiClient = axios.create({
  baseURL: SYNC_MICROSERVICE_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
