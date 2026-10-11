import { useQueryClient } from '@tanstack/react-query';
import { useDispatch } from 'react-redux';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { showInfoDialog } from '@/features/infoDialogSlice';
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
    onSuccess: (data) => {
      const { deleted_ids: deletedIds = [], failed_paths: failedPaths = [] } =
        data.data ?? {};

      // Drop only the ones that actually got deleted -- a path in
      // failed_paths means its row is still there, so it must keep showing.
      dispatch(removeImages(deletedIds));

      if (failedPaths.length > 0) {
        dispatch(
          showInfoDialog({
            title: 'Some Files Could Not Be Deleted',
            message: `The following file(s) could not be deleted from your device: ${failedPaths
              .map((path) => path.split('/').pop())
              .join(', ')}`,
            variant: 'error',
          }),
        );
      }

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
