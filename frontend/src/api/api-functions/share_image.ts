import { shareEndpoints } from "../apiEndpoints";
import { apiClient } from "../axiosConfig";
import { APIResponse } from "@/types/API";

interface ShareImageRequest{
    path: string;
}

interface ShareImageData{
    message: string;
    success: boolean;
}

export const shareImage = async(path: string): Promise<APIResponse> => {
    const response = await apiClient.post<APIResponse>(
        shareEndpoints.shareImage, 
        {path} as ShareImageRequest
    );
    return response.data.data as ShareImageData;
}