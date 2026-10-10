import { shareEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import type { BackendRes } from '@/hooks/useQueryExtension';
import { CreateShareRequest, Share } from '@/types/Share';

export const getShares = async (): Promise<BackendRes<Share[]>> => {
  const response = await apiClient.get(shareEndpoints.getShares);
  return response.data;
};

export const createShare = async (
  albumId: string,
  data: CreateShareRequest = {},
): Promise<BackendRes<Share>> => {
  const response = await apiClient.post(
    shareEndpoints.createShare(albumId),
    data,
  );
  return response.data;
};

// The network listener closes with the last share revoked.
export const revokeShare = async (token: string): Promise<BackendRes<null>> => {
  const response = await apiClient.delete(shareEndpoints.revokeShare(token));
  return response.data;
};
