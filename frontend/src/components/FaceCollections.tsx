import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { Card, CardContent } from '@/components/ui/card';
import { PersonAvatar } from '@/components/PersonAvatar';
import { getPersonName, getPhotoCountText } from '@/utils/personUtils';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, Users } from 'lucide-react';
import { MultiPersonSearchDialog } from '@/components/Dialog/MultiPersonSearchDialog';
import { RootState } from '@/app/store';
import { setClusters } from '@/features/faceClustersSlice';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllClusters } from '@/api/api-functions';
import { Cluster } from '@/types/Media';

interface FaceCollectionsProps {
  onSearchActivated?: (
    names: string[],
    matchMode: 'match_any' | 'match_all',
  ) => void;
}

// One row at xl:grid-cols-8. Keeps the card height fixed on every page,
// not just the default view.
const PAGE_SIZE = 8;

export function FaceCollections({ onSearchActivated }: FaceCollectionsProps) {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [isSearchDialogOpen, setIsSearchDialogOpen] = useState(false);
  const [page, setPage] = useState(0);

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

  // Highest face_count first, so the most prominent people show up on page 1.
  const sortedClusters = useMemo(
    () =>
      [...(clusters ?? [])].sort(
        (a: Cluster, b: Cluster) => (b.face_count ?? 0) - (a.face_count ?? 0),
      ),
    [clusters],
  );

  // Clamp page in case the cluster list shrinks (e.g. after a delete) while
  // the user is on a later page.
  const totalPages = Math.max(1, Math.ceil(sortedClusters.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages - 1);

  useEffect(() => {
    setPage((previousPage) => Math.min(previousPage, totalPages - 1));
  }, [totalPages]);

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

  const hasMultiplePages = totalPages > 1;
  const visibleClusters = sortedClusters.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  );

  return (
    <Card className="border-primary/20 w-full">
      <CardContent>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Face Collections</h2>
          <Button
            variant="outline"
            size="sm"
            className="cursor-pointer"
            onClick={() => setIsSearchDialogOpen(true)}
            title="Search multiple people at once"
          >
            <Users className="mr-2 h-4 w-4" />
            Search multiple people
          </Button>
        </div>
        <p className="text-muted-foreground mb-6">
          PictoPy has identified these people in your photos. Click on a person
          to see all their photos.
        </p>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
          {visibleClusters.map((cluster: Cluster) => (
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
          {Array.from({ length: PAGE_SIZE - visibleClusters.length }).map(
            (_, index) => (
              <div
                key={`placeholder-${index}`}
                className="flex flex-col items-center gap-2 rounded-lg p-4"
                inert
              >
                <div className="w-16 md:h-20 md:w-20" />
                <div className="text-center">
                  <p className="font-medium">&nbsp;</p>
                  <p className="text-muted-foreground text-xs">&nbsp;</p>
                </div>
              </div>
            ),
          )}
        </div>
        {hasMultiplePages && (
          <div className="mt-4 flex items-center justify-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              className="cursor-pointer"
              aria-label="Previous page"
              disabled={currentPage === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-muted-foreground text-sm">
              Page {currentPage + 1} of {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="cursor-pointer"
              aria-label="Next page"
              disabled={currentPage === totalPages - 1}
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
        <MultiPersonSearchDialog
          open={isSearchDialogOpen}
          onOpenChange={setIsSearchDialogOpen}
          onSearchActivated={onSearchActivated}
        />
      </CardContent>
    </Card>
  );
}
