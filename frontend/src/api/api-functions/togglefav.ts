import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';

export interface ToggleFavouriteResponse {
  success: boolean;
  image_id: string;
  isFavourite: boolean;
}

export const togglefav = async (
  image_id: string,
): Promise<ToggleFavouriteResponse> => {
  const response = await apiClient.post<ToggleFavouriteResponse>(
    imagesEndpoints.setFavourite,
    { image_id },
  );
  return response.data;
};
