import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { togglefav } from '@/api/api-functions/togglefav';

export const useTogglefavhook = () => {
  const toggleFavouriteMutation = usePictoMutation({
    mutationFn: async (image_id: string) => togglefav(image_id),
    autoInvalidateTags: ['images'],
  });
  useMutationFeedback(toggleFavouriteMutation, {
    showLoading: false,
  });
  return {
    toggleFavourite: (id: any) => toggleFavouriteMutation.mutate(id),
    toggleFavouritePending: toggleFavouriteMutation.isPending,
  };
};
