declare module '@tauri-apps/plugin-dialog' {
  export function save(options: {
    defaultPath?: string;
    title?: string;
    filters?: Array<{
      name: string;
      extensions: string[];
    }>;
  }): Promise<string | null>;
}

declare module '@tauri-apps/plugin-fs' {
  export function writeFile(filePath: string, data: Uint8Array): Promise<void>;
}

// Global declaration for checking Tauri environment
interface Window {
  __TAURI__?: {
    [key: string]: any;
  };
}
