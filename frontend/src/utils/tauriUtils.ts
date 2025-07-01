/**
 * Utility functions for Tauri environment detection and fallbacks
 */

// Check if we're running in a Tauri environment
export const isTauriEnvironment = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI__' in window;
};

// Safe invoke wrapper that only calls Tauri APIs when available
export const safeTauriInvoke = async (command: string, args?: any): Promise<any> => {
  if (!isTauriEnvironment()) {
    console.warn(`Tauri command "${command}" is not available in browser mode`);
    return null;
  }

  try {
    const { invoke } = await import('@tauri-apps/api/core');
    return await invoke(command, args);
  } catch (error) {
    console.error(`Error invoking Tauri command "${command}":`, error);
    throw error;
  }
};

// Safe updater check that only works in Tauri environment
export const safeTauriUpdaterCheck = async (): Promise<any> => {
  if (!isTauriEnvironment()) {
    console.warn('Updater is not available in browser mode');
    return null;
  }

  try {
    const { check } = await import('@tauri-apps/plugin-updater');
    return await check();
  } catch (error) {
    console.error('Error checking for updates:', error);
    return null;
  }
};

// Safe dialog open that only works in Tauri environment
export const safeTauriDialogOpen = async (options: any): Promise<string[] | string | null> => {
  if (!isTauriEnvironment()) {
    console.warn('File dialog is not available in browser mode');
    // In browser mode, we could potentially use the HTML5 file input as a fallback
    return null;
  }

  try {
    const { open } = await import('@tauri-apps/plugin-dialog');
    return await open(options);
  } catch (error) {
    console.error('Error opening dialog:', error);
    return null;
  }
};

// Safe convertFileSrc that returns a fallback URL in browser mode
export const safeTauriConvertFileSrc = (src: string): string => {
  if (!isTauriEnvironment()) {
    // In browser mode, return the src as-is or provide a fallback
    return src;
  }

  try {
    // Dynamic import to avoid errors in browser mode
    const { convertFileSrc } = require('@tauri-apps/api/core');
    return convertFileSrc(src);
  } catch (error) {
    console.error('Error converting file src:', error);
    return src;
  }
};

// Safe dialog save that only works in Tauri environment
export const safeTauriDialogSave = async (options: any): Promise<string | null> => {
  if (!isTauriEnvironment()) {
    console.warn('Save dialog is not available in browser mode');
    return null;
  }

  try {
    const { save } = await import('@tauri-apps/plugin-dialog');
    return await save(options);
  } catch (error) {
    console.error('Error opening save dialog:', error);
    return null;
  }
};

// Safe file read that only works in Tauri environment
export const safeTauriReadFile = async (path: string): Promise<Uint8Array | null> => {
  if (!isTauriEnvironment()) {
    console.warn('File reading is not available in browser mode');
    return null;
  }

  try {
    const { readFile } = await import('@tauri-apps/plugin-fs');
    return await readFile(path);
  } catch (error) {
    console.error('Error reading file:', error);
    return null;
  }
}; 