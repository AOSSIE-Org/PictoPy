declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
    __TAURI__?: unknown;
    isTauri?: boolean;
  }
}

export const isTauriEnvironment = (): boolean => {
  // window.isTauri is the official check, available since Tauri 2.0.0-beta.9.
  try {
    if (typeof window !== 'undefined' && window.isTauri) {
      return true;
    }
  } catch (error) {
    // Fall through to the manual checks below.
  }

  // Tauri v2 internals, for builds where isTauri is unset.
  if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
    return true;
  }

  // Older global, only present with withGlobalTauri: true.
  if (typeof window !== 'undefined' && '__TAURI__' in window) {
    return true;
  }

  return false;
};
