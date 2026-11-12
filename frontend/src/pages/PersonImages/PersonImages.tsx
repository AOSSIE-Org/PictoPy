import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useQueryClient } from '@tanstack/react-query';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { VideoCard } from '@/components/Media/VideoCard';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';
import { facePhotoToImage } from '@/utils/personUtils';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import {
  setCurrentViewIndex as setCurrentVideoViewIndex,
  setVideos,
} from '@/features/videoSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { updateClusterName } from '@/features/faceClustersSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { selectIsVideoViewOpen, selectVideos } from '@/features/videoSelectors';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { fetchClusterImages, renameCluster } from '@/api/api-functions';
import { useNavigate, useParams } from 'react-router';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Check, Pencil, ArrowLeft, X } from 'lucide-react';

export const PersonImages = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { clusterId } = useParams<{ clusterId: string }>();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);
  const isVideoViewOpen = useSelector(selectIsVideoViewOpen);
  const videos = useSelector(selectVideos);
  const [clusterName, setClusterName] = useState<string>('random_name');
  const [draftName, setDraftName] = useState<string>('');
  const [isEditing, setIsEditing] = useState<boolean>(false);

  const [loadedClusterId, setLoadedClusterId] = useState<string | undefined>(
    undefined,
  );
  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['person-images', clusterId],
    queryFn: async () => fetchClusterImages({ clusterId: clusterId || '' }),
  });

  const renameMutation = usePictoMutation({
    mutationFn: async ({
      targetClusterId,
      newName,
    }: {
      targetClusterId: string;
      newName: string;
    }) => renameCluster({ clusterId: targetClusterId, newName }),
    onSuccess: (_data, { targetClusterId, newName }) => {
      if (targetClusterId === clusterId) {
        setClusterName(newName);
        setIsEditing(false);
      }
      dispatch(
        updateClusterName({
          clusterId: targetClusterId,
          clusterName: newName,
        }),
      );
      void queryClient.invalidateQueries({ queryKey: ['clusters'] });
      void queryClient.invalidateQueries({
        queryKey: ['person-images', targetClusterId],
      });
    },
  });

  const feedbackOptions = useMemo(
    () => ({
      loadingMessage: 'Renaming person...',
      successTitle: 'Success',
      successMessage:
        renameMutation.successMessage || 'Person renamed successfully.',
      errorTitle: 'Error',
      errorMessage:
        renameMutation.errorMessage ||
        'Failed to rename person. Please try again.',
    }),
    [renameMutation.successMessage, renameMutation.errorMessage],
  );

  useMutationFeedback(renameMutation, feedbackOptions);

  useEffect(() => {
    setIsEditing(false);
  }, [clusterId]);

  useEffect(() => {
    if (isLoading) {
      dispatch(showLoader('Loading images'));
    } else if (isError) {
      dispatch(hideLoader());
    } else if (isSuccess) {
      const res = data?.data;
      dispatch(setImages((res?.images ?? []).map(facePhotoToImage)));
      dispatch(setVideos(res?.videos ?? []));
      setClusterName(res?.cluster_name || 'random_name');
      setLoadedClusterId(clusterId);
      dispatch(hideLoader());
    }
  }, [data, isSuccess, isError, isLoading, dispatch, clusterId]);

  // Fallback to query data until Redux slice syncs for this cluster (#1315)
  const personImages =
    clusterId !== undefined && loadedClusterId === clusterId
      ? images
      : (data?.data?.images ?? []).map(facePhotoToImage);
  const personVideos =
    clusterId !== undefined && loadedClusterId === clusterId
      ? videos
      : (data?.data?.videos ?? []);
  const displayName =
    clusterId !== undefined && loadedClusterId === clusterId
      ? clusterName
      : (data?.data?.cluster_name ?? 'random_name');

  const handleEditName = () => {
    setDraftName(displayName);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setDraftName(displayName);
    setIsEditing(false);
  };

  const handleSaveName = () => {
    if (!clusterId || renameMutation.isPending) return;

    const trimmedName = draftName.trim();
    if (!trimmedName) {
      dispatch(
        showInfoDialog({
          title: 'Invalid Name',
          message: 'Person name cannot be empty.',
          variant: 'error',
        }),
      );
      return;
    }

    if (trimmedName === displayName) {
      setIsEditing(false);
      return;
    }

    renameMutation.mutate({ targetClusterId: clusterId, newName: trimmedName });
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDraftName(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSaveName();
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };
  return (
    <div>
      <div className="my-6 flex items-center justify-between">
        <Button
          variant="outline"
          onClick={() => navigate(-1)} //Navigate 1 page back
          className="flex cursor-pointer items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>

        {isEditing ? (
          <div className="flex items-center gap-2">
            <Input
              value={draftName}
              onChange={handleNameChange}
              onKeyDown={handleKeyDown}
              disabled={renameMutation.isPending}
              className="max-w-xs"
              placeholder="Enter person name"
              aria-label="Person name"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleSaveName}
              disabled={renameMutation.isPending}
              aria-label="Save person name"
              className="h-10 w-10 cursor-pointer"
            >
              <Check className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={handleCancelEdit}
              disabled={renameMutation.isPending}
              aria-label="Cancel editing"
              className="h-10 w-10 cursor-pointer"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <Button
            variant="outline"
            onClick={handleEditName}
            className="flex cursor-pointer items-center gap-2"
          >
            <Pencil className="h-4 w-4" />
            Edit Name
          </Button>
        )}
      </div>
      <h1 className="mb-6 text-2xl font-bold">{displayName}</h1>
      <div className="grid grid-cols-1 gap-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {personImages.map((image, index) => (
          <div key={image.id} className="group relative">
            <ImageCard
              image={image}
              imageIndex={index}
              className="w-full transition-transform duration-200 group-hover:scale-105"
              onClick={() => dispatch(setCurrentViewIndex(index))}
            />
          </div>
        ))}
      </div>

      {/* Videos the same person was found in, via their keyframes */}
      {personVideos.length > 0 && (
        <>
          <h2 className="mb-4 text-xl font-semibold">Videos</h2>
          <div className="grid grid-cols-1 gap-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {personVideos.map((video, index) => (
              <div key={video.id} className="group relative">
                <VideoCard
                  video={video}
                  className="w-full transition-transform duration-200 group-hover:scale-105"
                  onClick={() => dispatch(setCurrentVideoViewIndex(index))}
                />
              </div>
            ))}
          </div>
        </>
      )}

      {/* Media Viewer Modals */}
      {isImageViewOpen && <MediaView images={personImages} />}
      {isVideoViewOpen && <VideoPlayerOverlay videos={personVideos} />}
    </div>
  );
};
