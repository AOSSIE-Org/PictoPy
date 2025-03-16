import { faceTaggingEndpoints } from '../apiEndpoints';

export const searchByFace = async (file: File, threshold: number = 0.5) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('threshold', threshold.toString());

  try {
    const response = await fetch(faceTaggingEndpoints.searchByFace, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.message || `Request failed with status ${response.status}`,
      );
    }

    return data;
  } catch (error) {
    console.error('Error searching by face:', error);
    throw error;
  }
};
