import { faceTaggingEndpoints } from "../apiEndpoints";

export const searchByFace = async (file: File, threshold: number = 0.5) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("threshold", threshold.toString());

  try {
    const response = await fetch(faceTaggingEndpoints.searchByFace, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error searching by face:", error);
    throw error;
  }
};