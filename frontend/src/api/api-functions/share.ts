import { shareEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import type { BackendRes } from '@/hooks/useQueryExtension';
import { CreateShareRequest, Share } from '@/types/Share';

/**
 * Every album currently being served on the local network
 */
export const getShares = async (): Promise<BackendRes<Share[]>> => {
  const response = await apiClient.get(shareEndpoints.getShares);
  return response.data;
};

/**
 * Start serving an album on the local network
 * @param albumId - Album UUID
 * @param data - Optional expiry and password
 */
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

/**
 * Stop serving a share. The network listener closes with the last one.
 * @param token - The share's token
 */
export const revokeShare = async (token: string): Promise<BackendRes<null>> => {
  const response = await apiClient.delete(shareEndpoints.revokeShare(token));
  return response.data;
};
