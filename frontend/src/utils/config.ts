export const getBackendUrl = (): string => {
  return process.env.VITE_BACKEND_URL || 'http://localhost:8000';
};
