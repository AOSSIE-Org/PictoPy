import { apiClient } from '../axiosConfig';

export const semanticSearch = async (query: string) => {
    const response = await apiClient.get(`/semantic/search?q=${encodeURIComponent(query)}`);
    return response.data;
};

export const triggerIndexing = async () => {
    const response = await apiClient.post('/semantic/index');
    return response.data;
};

export const getIndexingStatus = async () => {
    const response = await apiClient.get('/semantic/status');
    return response.data;
};
