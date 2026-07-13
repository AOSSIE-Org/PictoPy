import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllImages = async (
  tagged?: boolean,
): Promise<APIResponse> => {
  const params = tagged !== undefined ? { tagged } : {};
  const response = await apiClient.get<APIResponse>(
    imagesEndpoints.getAllImages,
    { params },
  );
  return response.data;
};

export interface SearchImagesByTagRequest {
  tag: string;
}

export const searchImagesByTag = async (
  request: SearchImagesByTagRequest,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    imagesEndpoints.searchByTag(request.tag),
  );
  return response.data;
};

export interface SemanticSearchImagesRequest {
  query: string;
}

export const semanticSearchImages = async (
  request: SemanticSearchImagesRequest,
): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    `/images/semantic-search?query=${encodeURIComponent(request.query)}`,
  );
  return response.data;
};
