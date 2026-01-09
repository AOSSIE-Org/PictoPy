import { usePictoQuery } from './useQueryExtension';
import { searchImages } from '@/api/api-functions/images';

export const useImageSearch = (query: string, enabled: boolean = true) => {
  return usePictoQuery({
    queryKey: ['images', 'search', query],
    queryFn: () => searchImages(query),
    enabled: enabled && query.length > 0,
  });
};
