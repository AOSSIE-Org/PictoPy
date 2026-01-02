import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { RootState } from '@/app/store';
import { setClusters } from '@/features/faceClustersSlice';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllClusters } from '@/api/api-functions';
import { Cluster } from '@/types/Media';

export function FaceCollections() {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const { clusters } = useSelector((state: RootState) => state.faceClusters);

  const {
    data: clustersData,
    isSuccess: clustersSuccess,
    isLoading: clustersLoading,
    isError: clustersError,
  } = usePictoQuery({
    queryKey: ['clusters'],
    queryFn: fetchAllClusters,
  });

  useEffect(() => {
    if (clustersSuccess && clustersData?.data?.clusters) {
      const clusters = (clustersData.data.clusters || []) as Cluster[];
      dispatch(setClusters(clusters));
    }
  }, [clustersData, clustersSuccess, dispatch]);

  const handlePersonClick = (clusterId: string) => {
    navigate(`/person/${clusterId}`);
  };

  if (clustersLoading) {
    return (
      <Card className="border-primary/20 w-full animate-pulse">
        <CardContent className="p-6">
          <h2 className="mb-4 text-xl font-semibold">Face Collections</h2>
          <div className="flex items-center justify-center p-8">
            <p className="text-muted-foreground italic">Detecting and grouping faces...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (clustersError) {
    return (
      <Card className="border-destructive/20 w-full">
        <CardContent className="p-6">
          <h2 className="mb-4 text-xl font-semibold text-destructive">Face Collections</h2>
          <p className="text-muted-foreground">
            Error loading face collections. Please try refreshing or checking the backend logs.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!clusters || clusters.length === 0) {
    return (
      <Card className="border-primary/20 w-full">
        <CardContent className="p-6">
          <h2 className="mb-4 text-xl font-semibold">Face Collections</h2>
          <p className="text-muted-foreground italic">
            No face collections detected yet. PictoPy will automatically group faces as you add more photos with AI tagging enabled.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-primary/20 w-full">
      <CardContent>
        <h2 className="mb-4 text-xl font-semibold">Face Collections</h2>
        <p className="text-muted-foreground mb-6">
          PictoPy has identified these people in your photos. Click on a person
          to see all their photos.
        </p>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
          {clusters.map((cluster: any) => (
            <div
              key={cluster.cluster_id}
              className="hover:bg-accent flex cursor-pointer flex-col items-center gap-2 rounded-lg p-4 transition-colors dark:hover:bg-white/10"
              onClick={() => handlePersonClick(cluster.cluster_id)}
            >
              <Avatar className="border-accent-foreground w-16 border-[1px] md:h-20 md:w-20">
                <AvatarImage
                  src={
                    cluster.face_image_base64
                      ? `data:image/jpeg;base64,${cluster.face_image_base64}`
                      : undefined
                  }
                  alt={cluster.cluster_name || 'Person'}
                />
                <AvatarFallback>
                  {cluster.cluster_name?.charAt(0).toUpperCase() ||
                    cluster.cluster_id.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="text-center">
                <p className="font-medium">
                  {cluster.cluster_name ||
                    `Person ${cluster.cluster_id.slice(-4)}`}
                </p>
                <p className="text-muted-foreground text-xs">
                  {cluster.face_count} photo
                  {cluster.face_count !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
