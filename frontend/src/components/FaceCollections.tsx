import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { Card, CardContent } from '@/components/ui/card';
import { PersonAvatar } from '@/components/PersonAvatar';
import { getPersonName, getPhotoCountText } from '@/utils/personUtils';
import { Button } from '@/components/ui/button';
import { Users } from 'lucide-react';
import { MultiPersonSearchDialog } from '@/components/Dialog/MultiPersonSearchDialog';
import { RootState } from '@/app/store';
import { setClusters } from '@/features/faceClustersSlice';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllClusters } from '@/api/api-functions';
import { Cluster } from '@/types/Media';

export function FaceCollections() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [isSearchDialogOpen, setIsSearchDialogOpen] = useState(false);

  const { clusters } = useSelector((state: RootState) => state.faceClusters);

  const { data: clustersData, isSuccess: clustersSuccess } = usePictoQuery({
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

  if (!clusters || clusters.length === 0) {
    return (
      <Card className="border-primary/20 w-full">
        <CardContent className="p-6">
          <h2 className="mb-4 text-xl font-semibold">Face Collections</h2>
          <p className="text-muted-foreground">
            No face collections found. PictoPy will automatically detect and
            group faces as you add more photos.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-primary/20 w-full">
      <CardContent>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Face Collections</h2>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 cursor-pointer p-1"
            onClick={() => setIsSearchDialogOpen(true)}
            title="Search by multiple people"
          >
            <Users className="h-4 w-4" />
            <span className="sr-only">Search by multiple people</span>
          </Button>
        </div>
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
              <PersonAvatar
                cluster={cluster}
                className="border-accent-foreground w-16 border-[1px] md:h-20 md:w-20"
              />
              <div className="text-center">
                <p className="font-medium">{getPersonName(cluster)}</p>
                <p className="text-muted-foreground text-xs">
                  {getPhotoCountText(cluster.face_count)}
                </p>
              </div>
            </div>
          ))}
        </div>
        <MultiPersonSearchDialog
          open={isSearchDialogOpen}
          onOpenChange={setIsSearchDialogOpen}
        />
      </CardContent>
    </Card>
  );
}
