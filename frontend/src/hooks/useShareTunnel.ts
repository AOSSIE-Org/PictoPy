import { useCallback, useRef, useState } from 'react';
import { startTunnel, stopTunnel, tunnelStatus } from '@/utils/tunnel';
import { ShareTunnel } from '@/types/Share';

// One tunnel forwards the whole share port, so it belongs to the app, not to an
// album. Asks the Rust side rather than trusting what a dialog last saw.
export const useShareTunnel = (): ShareTunnel => {
  const [url, setUrl] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  // Bumped whenever a tunnel is opened or closed. A status lookup started
  // before one of those is describing a tunnel that has since been replaced,
  // and applying its answer would wipe an address just obtained.
  const revision = useRef(0);
  const latest = useRef<string | null>(null);

  const apply = useCallback((value: string | null) => {
    latest.current = value;
    setUrl(value);
  }, []);

  const refresh = useCallback(async (): Promise<string | null> => {
    const startedAt = revision.current;
    const current = await tunnelStatus().catch(() => null);
    if (revision.current !== startedAt) {
      // Something newer finished while this was in flight; it knows better.
      return latest.current;
    }
    apply(current);
    return current;
  }, [apply]);

  const open = useCallback(
    async (port: number): Promise<string> => {
      revision.current += 1;
      const startedAt = revision.current;
      setIsConnecting(true);
      try {
        const opened = await startTunnel(port);
        if (revision.current !== startedAt) {
          // A close landed while this was starting. Honour it rather than
          // handing back a live public address nobody asked to keep.
          await stopTunnel().catch(() => undefined);
          throw new Error('The connection was closed while it was starting.');
        }
        apply(opened);
        return opened;
      } finally {
        setIsConnecting(false);
      }
    },
    [apply],
  );

  const close = useCallback(async (): Promise<void> => {
    revision.current += 1;
    // Unconditional: a start still in flight already has a killable child, and
    // checking first would read null and skip the stop. A no-op when idle.
    await stopTunnel();
    apply(null);
  }, [apply]);

  return { url, isConnecting, refresh, open, close };
};
