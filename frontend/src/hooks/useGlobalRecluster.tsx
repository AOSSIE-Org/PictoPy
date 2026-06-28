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
  const pollHandleRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [state, setState] = useState<ReclusterState>(idleState);

  const stopPolling = useCallback(() => {
    if (pollHandleRef.current) {
      clearInterval(pollHandleRef.current);
      pollHandleRef.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  const trigger = useCallback(() => {
    stopPolling();
    setState({ ...idleState, isPending: true });

    startGlobalReclustering()
      .then((startRes) => {
        const taskId = startRes.data?.task_id;
        if (!taskId) {
          throw new Error('Backend did not return a task_id for reclustering.');
        }

        pollHandleRef.current = setInterval(async () => {
          try {
            const statusRes = await getGlobalReclusterStatus(taskId);

            if (statusRes.data?.status === 'running') {
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
            stopPolling();
            setState({
              ...idleState,
              isError: true,
              error: err as Error,
              errorMessage: getErrorMessage(err),
            });
          }
        }, POLL_INTERVAL_MS);
      })
      .catch((err) => {
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
