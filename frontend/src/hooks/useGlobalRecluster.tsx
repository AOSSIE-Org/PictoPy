import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  startGlobalReclustering,
  getGlobalReclusterStatus,
  GlobalReclusterStatusData,
} from '@/api/api-functions/face_clusters';
import { getErrorMessage } from '@/lib/utils';

const POLL_INTERVAL_MS = 2000;

interface ReclusterState {
  isPending: boolean;
  isSuccess: boolean;
  isError: boolean;
  error: Error | undefined;
  successData: GlobalReclusterStatusData | undefined;
  successMessage: string | undefined;
  errorMessage: string | undefined;
}

const idleState: ReclusterState = {
  isPending: false,
  isSuccess: false,
  isError: false,
  error: undefined,
  successData: undefined,
  successMessage: undefined,
  errorMessage: undefined,
};

/**
 * Triggers global face reclustering and polls for completion.
 *
 * Reclustering runs over every face embedding in the library, so the
 * backend starts it as a background job and returns a task_id immediately
 * instead of blocking the HTTP request. This hook polls the job's status
 * endpoint until it reaches a terminal state.
 */
export function useGlobalRecluster() {
  const queryClient = useQueryClient();
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Identifies the latest trigger() call. A callback bails if a newer trigger
  // (or unmount) has since bumped this, so stale runs can't leak updates.
  const runIdRef = useRef(0);
  const [state, setState] = useState<ReclusterState>(idleState);

  const stopPolling = useCallback(() => {
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  }, []);

  // On unmount, invalidate any in-flight run and stop polling.
  useEffect(() => {
    return () => {
      runIdRef.current += 1;
      stopPolling();
    };
  }, [stopPolling]);

  const trigger = useCallback(() => {
    const runId = runIdRef.current + 1;
    runIdRef.current = runId;
    const isActive = () => runId === runIdRef.current;

    stopPolling();
    setState({ ...idleState, isPending: true });

    startGlobalReclustering()
      .then((startRes) => {
        if (!isActive()) return;

        const taskId = startRes.data?.task_id;
        if (!taskId) {
          throw new Error('Backend did not return a task_id for reclustering.');
        }

        // Self-scheduling poll: the next tick is only queued after the current
        // request resolves, so requests can't stack up or overlap.
        const poll = async () => {
          try {
            const statusRes = await getGlobalReclusterStatus(taskId);
            if (!isActive()) return;

            if (statusRes.data?.status === 'running') {
              pollTimeoutRef.current = setTimeout(poll, POLL_INTERVAL_MS);
              return;
            }

            stopPolling();
            queryClient.invalidateQueries({ queryKey: ['clusters'] });

            if (!statusRes.success || statusRes.data?.status === 'error') {
              setState({
                ...idleState,
                isError: true,
                error: new Error(
                  statusRes.message || 'Global reclustering failed.',
                ),
                errorMessage: statusRes.message,
              });
              return;
            }

            setState({
              ...idleState,
              isSuccess: true,
              successData: statusRes.data,
              successMessage: statusRes.message,
            });
          } catch (err) {
            if (!isActive()) return;
            stopPolling();
            setState({
              ...idleState,
              isError: true,
              error: err as Error,
              errorMessage: getErrorMessage(err),
            });
          }
        };

        poll();
      })
      .catch((err) => {
        if (!isActive()) return;
        setState({
          ...idleState,
          isError: true,
          error: err,
          errorMessage: getErrorMessage(err),
        });
      });
  }, [stopPolling, queryClient]);

  return { trigger, ...state };
}
