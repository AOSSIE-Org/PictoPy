import { userPreferencesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

// User Preferences Types
export interface UserPreferencesData {
  YOLO_model_size: 'nano' | 'small' | 'medium';
  GPU_Acceleration: boolean;
}

export interface GetUserPreferencesResponse extends APIResponse {
  user_preferences: UserPreferencesData;
}

export interface UpdateUserPreferencesRequest {
  YOLO_model_size?: 'nano' | 'small' | 'medium';
  GPU_Acceleration?: boolean;
}

export interface UpdateUserPreferencesResponse extends APIResponse {
  user_preferences: UserPreferencesData;
}

// API Functions
export const getUserPreferences =
  async (): Promise<GetUserPreferencesResponse> => {
    const response = await apiClient.get<GetUserPreferencesResponse>(
      userPreferencesEndpoints.getUserPreferences,
    );
    return response.data;
  };

export const updateUserPreferences = async (
  request: UpdateUserPreferencesRequest,
): Promise<UpdateUserPreferencesResponse> => {
  const response = await apiClient.put<UpdateUserPreferencesResponse>(
    userPreferencesEndpoints.updateUserPreferences,
    request,
  );
  return response.data;
};
