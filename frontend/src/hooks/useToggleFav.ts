import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { togglefav } from '@/api/api-functions/togglefav';
import { useDispatch } from 'react-redux';
import { updateImageFavoriteStatus } from '@/features/imageSlice';

export const useToggleFav = () => {
  const dispatch = useDispatch();
  
  const toggleFavouriteMutation = usePictoMutation({
    mutationFn: async (image_id: string) => togglefav(image_id),
    autoInvalidateTags: ['images'],
    onSuccess: (_data, image_id) => {
      
      dispatch(updateImageFavoriteStatus(image_id));
    },
  });
  useMutationFeedback(toggleFavouriteMutation, {
    showLoading: false,
    showSuccess: false,
  });
  return {
    toggleFavourite: (id: any) => toggleFavouriteMutation.mutate(id),
    toggleFavouritePending: toggleFavouriteMutation.isPending,
  };
};
