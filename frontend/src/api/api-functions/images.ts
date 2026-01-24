import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse, PaginatedAPIResponse } from '@/types/API';
import { Image } from '@/types/Media';

export interface FetchImagesParams {
  tagged?: boolean;
  page?: number;
  limit?: number;
}

/**
 * Fetch images from the API with optional pagination.
 *
 * @param params - Optional parameters for filtering and pagination
 * @param params.tagged - Filter by tagged status
 * @param params.page - Page number (1-indexed)
 * @param params.limit - Number of images per page
 * @returns APIResponse or PaginatedAPIResponse depending on whether pagination params are provided
 */
export const fetchAllImages = async (
  params?: FetchImagesParams | boolean,
): Promise<APIResponse | PaginatedAPIResponse<Image>> => {
  // Handle backward compatibility: if params is a boolean, treat it as tagged filter
  const queryParams: Record<string, unknown> = {};

  if (typeof params === 'boolean') {
    queryParams.tagged = params;
  } else if (params) {
    if (params.tagged !== undefined) {
      queryParams.tagged = params.tagged;
    }
    if (params.page !== undefined) {
      queryParams.page = params.page;
    }
    if (params.limit !== undefined) {
      queryParams.limit = params.limit;
    }
  }

  const response = await apiClient.get<
    APIResponse | PaginatedAPIResponse<Image>
  >(imagesEndpoints.getAllImages, { params: queryParams });
  return response.data;
};

/**
 * Fetch paginated images from the API.
 *
 * @param page - Page number (1-indexed)
 * @param limit - Number of images per page (default: 50)
 * @param tagged - Optional filter by tagged status
 * @returns PaginatedAPIResponse with images and pagination info
 */
export const fetchPaginatedImages = async (
  page: number,
  limit: number = 50,
  tagged?: boolean,
): Promise<PaginatedAPIResponse<Image>> => {
  const params: Record<string, unknown> = { page, limit };
  if (tagged !== undefined) {
    params.tagged = tagged;
  }

  const response = await apiClient.get<PaginatedAPIResponse<Image>>(
    imagesEndpoints.getAllImages,
    { params },
  );
  return response.data;
};
