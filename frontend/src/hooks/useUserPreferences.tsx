import { useState, useEffect } from 'react';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import {
  getUserPreferences,
  updateUserPreferences,
  UserPreferencesData,
} from '@/api/api-functions/user_preferences';
import { useMutationFeedback } from './useMutationFeedback';

/**
 * Custom hook for user preferences
 * Manages preferences state and mutation operations
 */
export const useUserPreferences = () => {
  const [preferences, setPreferences] = useState<UserPreferencesData>({
    YOLO_model_size: 'nano',
    GPU_Acceleration: false,
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

  // Apply feedback to the update preferences mutation
  useMutationFeedback(updatePreferencesMutation, {
    loadingMessage: 'Updating preferences',
    successTitle: 'Preferences Updated',
    successMessage: 'Your preferences have been saved successfully.',
    errorTitle: 'Update Error',
    errorMessage: 'Failed to update preferences. Please try again.',
  });

  /**
   * Update a specific preference
   */
  const updatePreference = (updatedPreferences: UserPreferencesData) => {
    setPreferences(updatedPreferences);
    updatePreferencesMutation.mutate(updatedPreferences);
  };

  /**
   * Update YOLO model size
   */
  const updateYoloModelSize = (size: 'nano' | 'small' | 'medium') => {
    const updatedPreferences = {
      ...preferences,
      YOLO_model_size: size,
    };
    updatePreference(updatedPreferences);
  };

  /**
   * Toggle GPU acceleration
   */
  const toggleGpuAcceleration = () => {
    const updatedPreferences = {
      ...preferences,
      GPU_Acceleration: !preferences.GPU_Acceleration,
    };
    updatePreference(updatedPreferences);
  };

  return {
    // Data
    preferences,
    isLoading: preferencesQuery.isLoading,

    // Operations
    updatePreference,
    updateYoloModelSize,
    toggleGpuAcceleration,

    // Mutation state (for use in UI, e.g., disabling buttons)
    isUpdating: updatePreferencesMutation.isPending,
  };
};

export default useUserPreferences;
