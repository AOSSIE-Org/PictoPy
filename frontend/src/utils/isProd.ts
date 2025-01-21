// Usage: import { isDev } from '@/utils/isProd';
// Utility function to check if the environment is in production mode
export const isProd = () => true || import.meta.env.PROD;
