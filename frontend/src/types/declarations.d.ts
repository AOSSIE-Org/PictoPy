// Tauri API declarations
declare module '@tauri-apps/api/core' {
  export function convertFileSrc(filePath: string, protocol?: string): string;
  export function invoke(
    cmd: string,
    args?: Record<string, unknown>,
  ): Promise<any>;
}
