import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { ScoredImage } from '@/types/Media';

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

export interface SemanticSearchAPIResponse extends APIResponse {
  data?: {
    images: ScoredImage[];
    total: number;
  };
}

export const semanticSearchImages = async (
  request: SemanticSearchImagesRequest,
): Promise<SemanticSearchAPIResponse> => {
  const response = await apiClient.get<SemanticSearchAPIResponse>(
    imagesEndpoints.semanticSearch(request.query),
  );
  return response.data;
};
