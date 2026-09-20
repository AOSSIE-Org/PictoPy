import { userPreferencesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

// User Preferences Types

/** Relative importance of each memory scoring signal. Normalized server-side. */
export interface MemoryScoringWeights {
  favourite: number;
  known_people: number;
  event_strength: number;
  face_presence: number;
  semantic_confidence: number;
  gps_novelty: number;
  in_album: number;
}

export interface MemoriesPreferences {
  enabled: boolean;
  notifications_enabled: boolean;
  /** The story viewer ships muted; audio is opt-in. */
  story_music_enabled: boolean;
  /** Seconds each photo is held before the story advances. */
  slide_duration_seconds: number;
  min_images: number;
  max_images: number;
  weights: MemoryScoringWeights;
}

export interface UserPreferencesData {
  YOLO_model_size: 'nano' | 'small' | 'medium';
  GPU_Acceleration: boolean;
  /** Seconds between sampled video keyframes when tagging videos. */
  Video_Frame_Interval: number;
  memories: MemoriesPreferences;
}

export interface GetUserPreferencesResponse extends APIResponse {
  user_preferences: UserPreferencesData;
}

export interface UpdateUserPreferencesRequest {
  YOLO_model_size?: 'nano' | 'small' | 'medium';
  GPU_Acceleration?: boolean;
  Video_Frame_Interval?: number;
  /** Partial: omitted keys keep their stored values. */
  memories?: Partial<Omit<MemoriesPreferences, 'weights'>> & {
    weights?: Partial<MemoryScoringWeights>;
  };
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
