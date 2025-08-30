import axios from 'axios';
import { BACKEND_URL } from '@/config/Backend';

// Create simple axios instance with basic configuration
export const apiClient = axios.create({
  baseURL: BACKEND_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
