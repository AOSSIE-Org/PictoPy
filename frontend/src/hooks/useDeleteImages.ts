import { useQueryClient } from '@tanstack/react-query';
import { useDispatch } from 'react-redux';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { deleteImages } from '@/api/api-functions/images';
import { removeImages } from '@/features/imageSlice';

interface DeleteImagesArgs {
  imageIds: string[];
  /** True also deletes each file from its folder on disk. */
  deleteFromDevice: boolean;
}

export const useDeleteImages = () => {
  const dispatch = useDispatch();
  const queryClient = useQueryClient();

  const deleteImagesMutation = usePictoMutation({
    mutationFn: async ({ imageIds, deleteFromDevice }: DeleteImagesArgs) =>
      deleteImages({
        image_ids: imageIds,
        delete_from_device: deleteFromDevice,
      }),
    autoInvalidateTags: ['images'],
    onSuccess: (data, { imageIds }) => {
      // Drop them from the store straight away so the viewer moves on instead of
      // waiting for the refetch. Fall back to what was asked for if the backend
      // response has no data, so the UI never keeps showing a deleted photo.
      dispatch(removeImages(data.data?.deleted_ids ?? imageIds));
      // Separate calls: autoInvalidateTags is passed through as a single queryKey
      // and matches by prefix, so neither of these matches ['images'].
      queryClient.invalidateQueries({ queryKey: ['album-images'] });
      queryClient.invalidateQueries({ queryKey: ['person-images'] });
    },
  });

  useMutationFeedback(deleteImagesMutation, {
    showLoading: false,
    showSuccess: false,
    errorTitle: 'Delete Failed',
    errorMessage: 'Could not delete the photo. Please try again.',
  });

  return {
    deleteImages: (args: DeleteImagesArgs) => deleteImagesMutation.mutate(args),
    deleteImagesPending: deleteImagesMutation.isPending,
  };
};
