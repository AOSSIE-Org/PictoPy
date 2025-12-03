import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { togglefav } from '@/api/api-functions/togglefav';
import { useQueryClient } from '@tanstack/react-query';

export const useToggleFav = () => {
  const queryClient = useQueryClient();
  
  const toggleFavouriteMutation = usePictoMutation({
    mutationFn: async (image_id: string) => togglefav(image_id),
    autoInvalidateTags: ['images'],
    onSuccess: () => {
      // Invalidate person-images queries to refetch cluster images
      queryClient.invalidateQueries({ queryKey: ['person-images'] });
    },
    onMutate: async (image_id: string) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['images'] });

      // Snapshot the previous value
      const previousImages = queryClient.getQueryData(['images']);

      // Optimistically update images query
      queryClient.setQueryData(['images'], (old: any) => {
        if (!old?.data) return old;
        
        return {
          ...old,
          data: old.data.map((img: any) => 
            img.id === image_id 
              ? { ...img, isFavourite: !img.isFavourite }
              : img
          )
        };
      });

      // Optimistically update person-images queries
      queryClient.setQueriesData({ queryKey: ['person-images'] }, (old: any) => {
        if (!old?.data?.images) return old;
        
        return {
          ...old,
          data: {
            ...old.data,
            images: old.data.images.map((img: any) => 
              img.id === image_id 
                ? { ...img, isFavourite: !img.isFavourite }
                : img
            )
          }
        };
      });

      return { previousImages };
    },
    onError: (err, image_id, context) => {
      if (context?.previousImages) {
        queryClient.setQueryData(['images'], context.previousImages);
      }
      // Refetch to restore correct state
      queryClient.invalidateQueries({ queryKey: ['person-images'] });
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