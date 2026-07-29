import { useState, useEffect } from 'react';
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
  notifications_enabled: true,
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

  // Query for user preferences
  const preferencesQuery = usePictoQuery({
    queryKey: ['userPreferences'],
    queryFn: getUserPreferences,
  });

  // Update local state when preferences data changes
  useEffect(() => {
    if (
      preferencesQuery.data?.success &&
      preferencesQuery.data.user_preferences
    ) {
      setPreferences(preferencesQuery.data.user_preferences);
    }
  }, [preferencesQuery.data]);

  // Mutation for updating user preferences
  const updatePreferencesMutation = usePictoMutation({
    mutationFn: updateUserPreferences,
    onSuccess: () => {
      // Invalidate and refetch preferences
      preferencesQuery.refetch();
    },
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

  /**
   * Update a specific preference
   */
  const updatePreference = async (updatedPreferences: UserPreferencesData) => {
    const previousPreferences = preferences;
    setPreferences(updatedPreferences);
    try {
      return await updatePreferencesMutation.mutateAsync(updatedPreferences);
    } catch (err) {
      setPreferences(previousPreferences);
      throw err;
    }
  };

  /**
   * Update YOLO model size
   */
  const updateYoloModelSize = async (size: 'nano' | 'small' | 'medium') => {
    const updatedPreferences = {
      ...preferences,
      YOLO_model_size: size,
    };
    return updatePreference(updatedPreferences);
  };

  /**
   * Toggle GPU acceleration
   */
  const toggleGpuAcceleration = async () => {
    const updatedPreferences = {
      ...preferences,
      GPU_Acceleration: !preferences.GPU_Acceleration,
    };
    return updatePreference(updatedPreferences);
  };

  /**
   * Update the video keyframe sampling interval (seconds)
   */
  const updateVideoFrameInterval = async (interval: number) => {
    const updatedPreferences = {
      ...preferences,
      Video_Frame_Interval: interval,
    };
    return updatePreference(updatedPreferences);
  };

  /**
   * Patch memories preferences.
   *
   * Sends only the changed keys rather than the whole preferences object, so
   * concurrent edits elsewhere in settings are not overwritten.
   */
  const updateMemoriesPreferences = async (
    patch: UpdateUserPreferencesRequest['memories'],
  ) => {
    const previousPreferences = preferences;
    setPreferences({
      ...preferences,
      memories: {
        ...preferences.memories,
        ...patch,
        weights: { ...preferences.memories.weights, ...patch?.weights },
      },
    });
    try {
      return await updatePreferencesMutation.mutateAsync({ memories: patch });
    } catch (err) {
      setPreferences(previousPreferences);
      throw err;
    }
  };

  return {
    // Data
    preferences,
    memoriesPreferences: preferences.memories ?? DEFAULT_MEMORIES_PREFERENCES,
    isLoading: preferencesQuery.isLoading,

    // Operations
    updatePreference,
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
