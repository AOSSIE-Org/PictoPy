import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { toggleVideoFav } from '@/api/api-functions/videos';
import { useDispatch } from 'react-redux';
import { updateVideoFavoriteStatus } from '@/features/videoSlice';

export const useToggleVideoFav = () => {
  const dispatch = useDispatch();

  const toggleFavouriteMutation = usePictoMutation({
    mutationFn: async (video_id: string) => toggleVideoFav(video_id),
    autoInvalidateTags: ['videos'],
    onSuccess: (_data, video_id) => {
      dispatch(updateVideoFavoriteStatus(video_id));
    },
  });
  useMutationFeedback(toggleFavouriteMutation, {
    showLoading: false,
    showSuccess: false,
  });
  return {
    toggleFavourite: (id: string) => toggleFavouriteMutation.mutate(id),
    toggleFavouritePending: toggleFavouriteMutation.isPending,
  };
};
