const API_BASE_URL = 'http://localhost:52123';

export interface UserPreferences {
  YOLO_model_size: string;
  GPU_Acceleration: boolean;
  avatar?: string;
}

export interface AvatarUploadResponse {
  success: boolean;
  message: string;
  avatar_url: string;
}

export const avatarApi = {
  async uploadAvatar(file: File): Promise<AvatarUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/avatars/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Upload failed');
    }

    return response.json();
  },

  async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/user-preferences/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(preferences),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Update failed');
    }
  },

  async getUserPreferences(): Promise<{ user_preferences: UserPreferences }> {
    const response = await fetch(`${API_BASE_URL}/user-preferences/`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch user preferences');
    }

    return response.json();
  },

  getAvatarUrl(avatarPath: string): string {
    if (avatarPath.startsWith('/avatars/uploads/')) {
      return `${API_BASE_URL}${avatarPath}`;
    }
    return avatarPath; // Preset avatar
  }
};