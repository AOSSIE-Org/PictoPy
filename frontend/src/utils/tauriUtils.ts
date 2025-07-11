/**
 * Utility functions for Tauri environment detection
 */

// Type declarations for Tauri window properties
declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
    __TAURI__?: unknown;
    isTauri?: boolean;
  }
}

// Check if we're running in a Tauri environment
export const isTauriEnvironment = (): boolean => {
  // Method 1: Use official Tauri API (recommended)
  try {
    // This is the official way to detect Tauri environment
    // Available since Tauri 2.0.0-beta.9
    if (typeof window !== 'undefined' && window.isTauri) {
      return true;
    }
  } catch (error) {
    // Fallback to manual detection if official API fails
  }

  // Method 2: Check for __TAURI_INTERNALS__ (Tauri v2 manual detection)
  if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
    return true;
  }
  
  // Method 3: Fallback to __TAURI__ for backward compatibility (requires withGlobalTauri: true)
  if (typeof window !== 'undefined' && '__TAURI__' in window) {
    return true;
  }
  
  return false;
};

// Alternative: You can also use the official API directly
export const isTauriEnvironmentOfficial = async (): Promise<boolean> => {
  try {
    const { isTauri } = await import('@tauri-apps/api/core');
    return isTauri();
  } catch (error) {
    // Fallback if @tauri-apps/api is not available
    return isTauriEnvironment();
  }
};
