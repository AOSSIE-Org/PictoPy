import { imagesEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { Image, ScoredImage } from '@/types/Media';

export interface GetAllImagesResponse extends APIResponse {
  data?: Image[];
}

export const fetchAllImages = async (
  tagged?: boolean,
): Promise<GetAllImagesResponse> => {
  const params = tagged !== undefined ? { tagged } : {};
  const response = await apiClient.get<GetAllImagesResponse>(
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

export interface DeleteImagesRequest {
  image_ids: string[];
  /** True also deletes each file from its folder on disk. */
  delete_from_device: boolean;
}

export interface DeleteImagesAPIResponse extends APIResponse {
  data?: {
    deleted_ids: string[];
    failed_paths: string[];
  };
}

export const deleteImages = async (
  request: DeleteImagesRequest,
): Promise<DeleteImagesAPIResponse> => {
  const response = await apiClient.delete<DeleteImagesAPIResponse>(
    imagesEndpoints.deleteImages,
    { data: request },
  );
  return response.data;
};
