import { useState, useEffect, useRef } from 'react';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import {
  getUserPreferences,
  updateUserPreferences,
  MemoriesPreferences,
  UpdateUserPreferencesRequest,
  UserPreferencesData,
} from '@/api/api-functions/user_preferences';
import { useMutationFeedback } from './useMutationFeedback';

export const DEFAULT_MEMORIES_PREFERENCES: MemoriesPreferences = {
  enabled: true,
  notifications_enabled: false,
  story_music_enabled: false,
  slide_duration_seconds: 5,
  min_images: 5,
  max_images: 30,
  weights: {
    favourite: 0.22,
    known_people: 0.2,
    event_strength: 0.18,
    face_presence: 0.12,
    semantic_confidence: 0.1,
    gps_novelty: 0.1,
    in_album: 0.08,
  },
};

/**
 * Custom hook for user preferences
 * Manages preferences state and mutation operations
 */
export const useUserPreferences = () => {
  const [preferences, setPreferences] = useState<UserPreferencesData>({
    YOLO_model_size: 'nano',
    GPU_Acceleration: false,
    Video_Frame_Interval: 5,
    memories: DEFAULT_MEMORIES_PREFERENCES,
  });

  // Writes read and roll back against this rather than `preferences`, which is
  // a render-old snapshot for anything already in flight.
  const preferencesRef = useRef(preferences);

  const applyPreferences = (next: UserPreferencesData) => {
    preferencesRef.current = next;
    setPreferences(next);
  };

  // Non-zero from the moment a write is queued until it settles.
  const pendingWrites = useRef(0);
  // Bumped when a write is queued. Any read already in flight at that point
  // describes the server from before it, however late the response arrives,
  // which is why this counts reads rather than timing them: a read that starts
  // first can still finish last.
  const writeEpoch = useRef(0);
  const readEpoch = useRef(0);

  // Query for user preferences
  const preferencesQuery = usePictoQuery({
    queryKey: ['userPreferences'],
    queryFn: () => {
      readEpoch.current = writeEpoch.current;
      return getUserPreferences();
    },
  });

  // Update local state when preferences data changes
  useEffect(() => {
    // Applying stale server state would revert the write and hand the next
    // queued one a stale base to build on.
    if (pendingWrites.current > 0) return;
    if (readEpoch.current !== writeEpoch.current) return;
    if (
      preferencesQuery.data?.success &&
      preferencesQuery.data.user_preferences
    ) {
      applyPreferences(preferencesQuery.data.user_preferences);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preferencesQuery.data]);

  // Mutation for updating user preferences. It does not refetch on success:
  // the response already carries the merged result, and reconciling inside the
  // queue is what keeps a stale read from overtaking a newer write.
  const updatePreferencesMutation = usePictoMutation({
    mutationFn: updateUserPreferences,
  });

  // Apply feedback to the update preferences mutation but hide loader and success dialog
  useMutationFeedback(updatePreferencesMutation, {
    showLoading: false, // Don't show the loading indicator to prevent flicker
    loadingMessage: 'Updating preferences',
    showSuccess: false, // Don't show the success InfoDialog
    successTitle: 'Preferences Updated',
    successMessage: 'Your preferences have been saved successfully.',
    errorTitle: 'Update Error',
    errorMessage: 'Failed to update preferences. Please try again.',
  });

  // One write at a time. Concurrent PUTs race on the server, and a rollback
  // captured while another write is in flight restores that write's optimistic
  // value rather than what is actually stored.
  const writeQueue = useRef<Promise<unknown>>(Promise.resolve());

  /**
   * Apply a change optimistically and send it, queued behind any write already
   * running.
   *
   * `build` runs when the write reaches the front of the queue, not when it was
   * requested, so a queued change is computed from what actually landed before
   * it. It returns the full next state and the request body, which carries only
   * the changed keys so a concurrent edit elsewhere in settings survives.
   */
  const writePreferences = (
    build: (current: UserPreferencesData) => {
      next: UserPreferencesData;
      request: UpdateUserPreferencesRequest;
    },
  ) => {
    // Counted here rather than in `send` so a load cannot slip in between the
    // click and the write reaching the front of the queue.
    pendingWrites.current += 1;
    writeEpoch.current += 1;

    const send = async () => {
      const current = preferencesRef.current;
      const { next, request } = build(current);
      applyPreferences(next);
      try {
        const response = await updatePreferencesMutation.mutateAsync(request);
        // The PUT returns the merged, validated result. Adopting it here keeps
        // reconciliation inside the queue, where nothing else is in flight.
        if (response?.success && response.user_preferences) {
          applyPreferences(response.user_preferences);
        }
        return response;
      } catch (err) {
        applyPreferences(current);
        throw err;
      } finally {
        pendingWrites.current -= 1;
      }
    };

    const result = writeQueue.current.then(send, send);
    // A rejected write must not stall every later one.
    writeQueue.current = result.catch(() => undefined);
    return result;
  };

  /**
   * Update YOLO model size
   */
  const updateYoloModelSize = async (size: 'nano' | 'small' | 'medium') =>
    writePreferences((current) => ({
      next: { ...current, YOLO_model_size: size },
      request: { YOLO_model_size: size },
    }));

  /**
   * Toggle GPU acceleration
   */
  const toggleGpuAcceleration = async () =>
    writePreferences((current) => {
      const GPU_Acceleration = !current.GPU_Acceleration;
      return {
        next: { ...current, GPU_Acceleration },
        request: { GPU_Acceleration },
      };
    });

  /**
   * Update the video keyframe sampling interval (seconds)
   */
  const updateVideoFrameInterval = async (interval: number) =>
    writePreferences((current) => ({
      next: { ...current, Video_Frame_Interval: interval },
      request: { Video_Frame_Interval: interval },
    }));

  /**
   * Patch memories preferences.
   */
  const updateMemoriesPreferences = async (
    patch: UpdateUserPreferencesRequest['memories'],
  ) =>
    writePreferences((current) => ({
      next: {
        ...current,
        memories: {
          ...current.memories,
          ...patch,
          weights: { ...current.memories.weights, ...patch?.weights },
        },
      },
      request: { memories: patch },
    }));

  return {
    // Data
    preferences,
    memoriesPreferences: preferences.memories ?? DEFAULT_MEMORIES_PREFERENCES,
    isLoading: preferencesQuery.isLoading,

    // Operations
    updateYoloModelSize,
    toggleGpuAcceleration,
    updateVideoFrameInterval,
    updateMemoriesPreferences,

    // For refetching preferences after external events (e.g., Model Manager window closing)
    refetch: preferencesQuery.refetch,

    // Mutation state (for use in UI, e.g., disabling buttons)
    isUpdating: updatePreferencesMutation.isPending,
  };
};

export default useUserPreferences;
