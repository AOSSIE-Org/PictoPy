import {apiClient} from '../axiosConfig';

export const scanCelebrities = async () => {
  const response = await apiClient.post('/celebrity/scan');
  return response.data;
};
