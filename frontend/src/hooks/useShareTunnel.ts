import { useCallback, useState } from 'react';
import { startTunnel, stopTunnel, tunnelStatus } from '@/utils/tunnel';

/**
 * The tunnel that makes the share server reachable off the LAN.
 *
 * One tunnel forwards the whole share port, so it belongs to the application
 * rather than to any one album. This owns the view of it, and deliberately
 * asks the Rust side rather than trusting what a dialog last saw: a share can
 * be stopped before the first status lookup has even resolved.
 */
export const useShareTunnel = () => {
  const [url, setUrl] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  /** The tunnel's current address, or null. Never throws. */
  const refresh = useCallback(async (): Promise<string | null> => {
    const current = await tunnelStatus().catch(() => null);
    setUrl(current);
    return current;
  }, []);

  /** Open a tunnel to the share port. Rejects if no provider answers. */
  const open = useCallback(async (port: number): Promise<string> => {
    setIsConnecting(true);
    try {
      const opened = await startTunnel(port);
      setUrl(opened);
      return opened;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  /**
   * Close the tunnel if one is running. Rejects if it could not be closed, so
   * the caller can say so rather than reporting a cleanup that did not happen.
   */
  const close = useCallback(async (): Promise<void> => {
    // Asked fresh instead of read from state above. If the lookup itself
    // fails, attempt the stop anyway: leaving a tunnel up is the worse of the
    // two mistakes.
    const current = await tunnelStatus().catch(() => 'unknown');
    if (current === null) {
      setUrl(null);
      return;
    }
    await stopTunnel();
    setUrl(null);
  }, []);

  return { url, isConnecting, refresh, open, close };
};
