import { foldersEndpoints } from '../apiEndpoints';
import { apiClient, syncApiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';
import { FolderTaggingStatusResponse } from '@/types/FolderStatus';

// Request Types
export interface AddFolderRequest {
  folder_path: string;
  parent_folder_id?: string;
  taggingCompleted?: boolean;
}

export interface UpdateAITaggingRequest {
  folder_ids: string[];
}

export interface DeleteFoldersRequest {
  folder_ids: string[];
}

export interface SyncFolderRequest {
  folder_path: string;
  folder_id: string;
}

// API Functions
export const getAllFolders = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    foldersEndpoints.getAllFolders,
  );
  return response.data;
};

export const addFolder = async (
  request: AddFolderRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    foldersEndpoints.addFolder,
    request,
  );
  return response.data;
};

export const enableAITagging = async (
  request: UpdateAITaggingRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    foldersEndpoints.enableAITagging,
    request,
  );
  return response.data;
};

export const disableAITagging = async (
  request: UpdateAITaggingRequest,
): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(
    foldersEndpoints.disableAITagging,
    request,
  );
  return response.data;
};

export const deleteFolders = async (
  request: DeleteFoldersRequest,
): Promise<APIResponse> => {
  const response = await apiClient.delete<APIResponse>(
    foldersEndpoints.deleteFolders,
    { data: request },
  );
  return response.data;
};

export const getFoldersTaggingStatus = async (): Promise<APIResponse> => {
  const response = await syncApiClient.get<FolderTaggingStatusResponse>(
    foldersEndpoints.getTaggingStatus,
  );
  const res = response.data;
  return {
    data: res.data as any,
    success: res.status === 'success',
    message: res.message,
  };
};
