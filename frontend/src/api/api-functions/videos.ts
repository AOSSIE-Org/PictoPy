import { videosEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

export const fetchAllVideos = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(
    videosEndpoints.getAllVideos,
  );
  return response.data;
};

export const uploadVideos = async (files: File[]): Promise<APIResponse> => {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const response = await apiClient.post<APIResponse>(
    videosEndpoints.upload,
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    },
  );
  return response.data;
};

export const scanVideos = async (): Promise<APIResponse> => {
  const response = await apiClient.post<APIResponse>(videosEndpoints.scan);
  return response.data;
};
