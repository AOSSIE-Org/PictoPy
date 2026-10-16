import { invoke } from '@tauri-apps/api/core';

// One SSH tunnel forwards the whole share port, so it serves every share rather
// than one album. Rust owns it and closes it on exit.

/** Open a tunnel to the share port, or return the URL of the one already up. */
export const startTunnel = (port: number): Promise<string> =>
  invoke<string>('tunnel_start', { port });

export const stopTunnel = (): Promise<void> => invoke<void>('tunnel_stop');

/** The public URL if a tunnel is running, null once it has gone away. */
export const tunnelStatus = (): Promise<string | null> =>
  invoke<string | null>('tunnel_status');
