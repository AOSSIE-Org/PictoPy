import React, { useCallback, useEffect, useState } from 'react';
import { Sparkles, X } from 'lucide-react';
import { useNavigate } from 'react-router';
import { useQueryClient } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { ROUTES } from '@/constants/routes';
import { MEMORIES_QUERY_KEY } from '@/hooks/useMemories';
import { openMemory } from '@/features/memoriesSlice';
import { useAppDispatch } from '@/store/hooks';

/** Payload of `memory:pending`, emitted by the Rust curation task. */
export interface PendingMemory {
  memory_id: string;
  title: string;
  subtitle: string | null;
  image_count: number;
  video_count: number;
}

const summarize = ({
  title,
  subtitle,
  image_count,
  video_count,
}: PendingMemory) =>
  [title, subtitle, `${image_count + video_count} items`]
    .filter(Boolean)
    .join(' · ');

/**
 * Bridges the desktop shell's memory events into the app.
 *
 * The Rust task emits `memory:pending` whether or not it raised a system
 * notification, because desktop notification clicks are not dependable across
 * platforms - this in-app card is the path that always works. Needs router
 * context, so it lives inside the router in App.
 */
export const MemoryNotificationListener: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pending, setPending] = useState<PendingMemory | null>(null);

  const show = useCallback(
    (memoryId: string) => {
      setPending(null);
      // Curation ran while the grid was on screen, so its list is stale.
      void queryClient.invalidateQueries({
        queryKey: [...MEMORIES_QUERY_KEY, 'list'],
      });
      dispatch(openMemory(memoryId));
      navigate(`/${ROUTES.MEMORIES}`);
    },
    [dispatch, navigate, queryClient],
  );

  useEffect(() => {
    let cancelled = false;

    const subscriptions = [
      listen<PendingMemory>('memory:pending', (event) =>
        setPending(event.payload),
      ),
      listen<{ memory_id: string }>('memory:open', (event) =>
        show(event.payload.memory_id),
      ),
    ];

    // The task can finish before React mounts when the backend is already up,
    // and an event with nobody listening is lost. Collect anything waiting.
    void invoke<PendingMemory | null>('take_pending_memory')
      .then((memory) => {
        if (!cancelled && memory) setPending(memory);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
      subscriptions.forEach((subscription) => {
        void subscription.then((unlisten) => unlisten()).catch(() => {});
      });
    };
  }, [show]);

  // Routed through Rust so the window is focused first and every entry point
  // lands on the same event. Falls back to routing here if the command is
  // unavailable, as it is outside the desktop shell.
  const handleOpen = useCallback(
    (memoryId: string) => {
      void invoke('open_memory', { memoryId }).catch(() => show(memoryId));
    },
    [show],
  );

  if (!pending) return null;

  return (
    <div className="fixed right-4 bottom-4 z-50 w-96 max-w-[calc(100vw-2rem)]">
      <Alert className="shadow-lg" role="status" aria-live="polite">
        <Sparkles className="text-blue-500" />
        <AlertTitle className="pr-6">Your Daily Memory is Ready</AlertTitle>
        <AlertDescription className="w-full">
          <span>{summarize(pending)}</span>
          <Button
            size="sm"
            className="mt-2 cursor-pointer"
            onClick={() => handleOpen(pending.memory_id)}
          >
            View memory
          </Button>
        </AlertDescription>
        <button
          type="button"
          aria-label="Dismiss memory notification"
          className="text-muted-foreground hover:text-foreground absolute top-3 right-3 cursor-pointer"
          onClick={() => setPending(null)}
        >
          <X className="h-4 w-4" />
        </button>
      </Alert>
    </div>
  );
};
