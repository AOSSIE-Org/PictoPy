import { useDispatch } from 'react-redux';
import { useMutation } from '@tanstack/react-query';
import { softDeleteImages } from '@/api/api-functions';
import {
  markImagesAsDeleted,
  setUndoState,
} from '@/features/imageSlice';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export const useDeleteImage = () => {
  const dispatch = useDispatch();

  const mutation = useMutation({
    mutationFn: (imageId: string) => softDeleteImages([imageId]),

    onSuccess: (_data, imageId) => {
      dispatch(markImagesAsDeleted([imageId]));
      dispatch(setUndoState([imageId]));
    },
  });

  useMutationFeedback(mutation, {
    loadingMessage: 'Deleting image...',
    successMessage: 'Image moved to Recently Deleted',
    showSuccess: true,
  });

  return {
    deleteSingleImage: mutation.mutate,
    isDeleting: mutation.isPending,
  };
};
