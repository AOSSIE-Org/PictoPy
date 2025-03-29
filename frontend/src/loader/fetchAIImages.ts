import { APIResponse } from "@/types/image";
import { imagesEndpoints } from "../../api/apiEndpoints";
import { parseAndSortImageData } from "../../api/api-functions/images";

export const fetchAllImageObjects = async () => {
  const response = await fetch(imagesEndpoints.allImageObjects);
  const data: APIResponse = await response.json();
  const parsedAndSortedImages = parseAndSortImageData(data.data);
  const newObj = {
    data: parsedAndSortedImages,
    success: data.success,
    error: data?.error,
    message: data?.message,
  };
  return newObj.data;
};
