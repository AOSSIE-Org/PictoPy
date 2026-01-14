import { apiClient } from '../axiosConfig';

export const semanticSearch = async (query: string) => {
    const response = await apiClient.get(`/semantic/search?q=${encodeURIComponent(query)}`);
    return response.data;
};

export const triggerIndexing = async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/semantic/index');
    return response.data;
};

export interface IndexingStatus {
    is_active: boolean;
    current: number;
    total: number;
    error: string | null;
}

export const getIndexingStatus = async (): Promise<IndexingStatus> => {
    const response = await apiClient.get('/semantic/status');
    return response.data;
};
