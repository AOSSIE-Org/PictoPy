import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { Image } from '@/types/Media';

export interface FetchAllImagesParams {
  tagged?: boolean;
  limit?: number;
  offset?: number;
}

export const fetchAllImages = async (
  params?: FetchAllImagesParams,
): Promise<APIResponse<Image[]>> => {
  const queryParams: Record<string, any> = {};
  
  if (params?.tagged !== undefined) {
    queryParams.tagged = params.tagged;
  }
  if (params?.limit !== undefined) {
    queryParams.limit = params.limit;
  }
  if (params?.offset !== undefined) {
    queryParams.offset = params.offset;
  }

  const response = await apiClient.get<APIResponse<Image[]>>(
    imagesEndpoints.getAllImages,
    { params: queryParams },
  );
  return response.data;
};
