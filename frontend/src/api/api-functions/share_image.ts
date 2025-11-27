import { shareEndpoints } from "../apiEndpoints";
import { apiClient } from "../axiosConfig";
import { APIResponse } from "@/types/API";

interface ShareImageRequest {
    image_id: string;  // Changed to string to match backend
}

interface ShareImageData {
    message: string;
    success: boolean;
}

export const shareImage = async (imageId: string): Promise<ShareImageData> => {
    const response = await apiClient.post<APIResponse>(
        shareEndpoints.shareImage, 
        { image_id: imageId } as ShareImageRequest
    );
    return response.data.data as ShareImageData;
}