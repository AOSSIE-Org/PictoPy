import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';
import { Image } from '@/types/Media';
import { setCurrentViewIndex, setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import { fetchClusterImages, renameCluster } from '@/api/api-functions';
import { useNavigate, useParams } from 'react-router';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ROUTES } from '@/constants/routes';
import { Check, Pencil, ArrowLeft } from 'lucide-react';

export const PersonImages = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { clusterId } = useParams<{ clusterId: string }>();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);
  const [clusterName, setClusterName] = useState<string>('random_name');
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['person-images', clusterId],
    queryFn: async () => fetchClusterImages({ clusterId: clusterId || '' }),
  });

  const { mutate: renameClusterMutate } = usePictoMutation({
    mutationFn: async (newName: string) =>
      renameCluster({ clusterId: clusterId || '', newName }),
  });

  useEffect(() => {
    if (isLoading) {
      dispatch(showLoader('Loading images'));
    } else if (isError) {
      dispatch(hideLoader());
    } else if (isSuccess) {
      const res: any = data?.data;
      const images = (res?.images || []) as Image[];
      dispatch(setImages(images));
      setClusterName(res?.cluster_name || 'random_name');
      dispatch(hideLoader());
    }
  }, [data, isSuccess, isError, isLoading, dispatch]);

  const handleEditName = () => {
    setClusterName(clusterName);
    setIsEditing(true);
  };

  const handleSaveName = () => {
    setClusterName(clusterName);
    renameClusterMutate(clusterName);
    setIsEditing(false);
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setClusterName(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSaveName();
    }
  };
  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <Button
          variant="outline"
          onClick={() => navigate(`/${ROUTES.AI}`)}
          className="flex cursor-pointer items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to AI Tagging
        </Button>

        {isEditing ? (
          <div className="flex items-center gap-2">
            <Input
              value={clusterName}
              onChange={handleNameChange}
              onKeyDown={handleKeyDown}
              className="max-w-xs"
              placeholder="Enter person name"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleSaveName}
              className="h-10 w-10 cursor-pointer"
            >
              <Check className="h-4 w-4" />
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
      <h1 className="mb-6 text-2xl font-bold">{clusterName}</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {images.map((image, index) => (
          <ImageCard
            key={image.id}
            image={image}
            imageIndex={index}
            className="w-full"
            onClick={() => dispatch(setCurrentViewIndex(index))}
          />
        ))}
      </div>

      {/* Media Viewer Modal */}
      {isImageViewOpen && <MediaView images={images} />}
    </div>
  );
};
