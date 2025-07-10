/**
 * Utility functions for Tauri environment detection
 */

// Check if we're running in a Tauri environment
export const isTauriEnvironment = (): boolean => {
  // return typeof window !== 'undefined' && '__TAURI__' in window;
  return true;
};
