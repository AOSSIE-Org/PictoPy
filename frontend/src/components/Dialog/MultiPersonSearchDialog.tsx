import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { cn } from '@/lib/utils';
import { RootState } from '@/app/store';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { PersonAvatar } from '@/components/PersonAvatar';
import { getPersonName, getPhotoCountText } from '@/utils/personUtils';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import {
  fetchMultiPersonSearch,
  MultiPersonSearchRequest,
} from '@/api/api-functions/face_clusters';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import type { Image, Cluster } from '@/types/Media';

interface MultiPersonSearchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSearchActivated?: (peopleNames: string[]) => void;
}

export function MultiPersonSearchDialog({
  open,
  onOpenChange,
  onSearchActivated,
}: MultiPersonSearchDialogProps) {
  const dispatch = useDispatch();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [matchMode, setMatchMode] = useState<'match_any' | 'match_all'>(
    'match_any',
  );

  const { clusters } = useSelector((state: RootState) => state.faceClusters);

  const { mutate } = usePictoMutation({
    mutationFn: async (req: MultiPersonSearchRequest) =>
      fetchMultiPersonSearch(req),
    onSuccess: (data) => {
      const images = data?.data?.images;
      dispatch(hideLoader());

      if (!images || images.length === 0) {
        dispatch(
          showInfoDialog({
            title: 'No Matches Found',
            message: 'No photos found for the selected people.',
            variant: 'info',
          }),
        );
        return;
      }

      const mappedImages = images.map((img: any) => ({
        id: img.id,
        path: img.path,
        thumbnailPath: img.thumbnailPath || '',
        metadata: img.metadata,
        folder_id: '',
        isTagged: true,
      })) as Image[];

      const selectedNames = [...selectedIds]
        .map((id) => {
          const cluster = clusters.find((c) => c.cluster_id === id);
          return cluster ? getPersonName(cluster) : null;
        })
        .filter((name): name is string => name !== null);

      dispatch(setImages(mappedImages));
      onSearchActivated?.(selectedNames);
      onOpenChange(false);
    },
    onError: () => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Search Failed',
          message: 'There was an error while searching for faces.',
          variant: 'error',
        }),
      );
    },
  });

  useEffect(() => {
    if (!open) {
      setSelectedIds(new Set());
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Search by Multiple People</DialogTitle>
          <DialogDescription>
            Select one or more people to find photos containing them.
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-4">
          <span className="text-muted-foreground text-sm">
            Show photos with:
          </span>
          <RadioGroup
            value={matchMode}
            onValueChange={(v) => setMatchMode(v as typeof matchMode)}
            className="flex gap-4"
          >
            <div className="flex items-center gap-2">
              <RadioGroupItem value="match_any" id="match_any" />
              <Label htmlFor="match_any" className="cursor-pointer text-sm">
                Any selected person
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <RadioGroupItem value="match_all" id="match_all" />
              <Label htmlFor="match_all" className="cursor-pointer text-sm">
                All selected people
              </Label>
            </div>
          </RadioGroup>
        </div>

        {selectedIds.size > 0 && (
          <div className="flex flex-wrap gap-2">
            {[...selectedIds].map((id) => {
              const cluster = clusters.find((c) => c.cluster_id === id);
              if (!cluster) return null;
              return (
                <Badge
                  key={id}
                  variant="secondary"
                  className="cursor-pointer gap-1"
                  onClick={() =>
                    setSelectedIds((prev) => {
                      const next = new Set(prev);
                      next.delete(id);
                      return next;
                    })
                  }
                >
                  {getPersonName(cluster)}
                  <span className="ml-1">×</span>
                </Badge>
              );
            })}
          </div>
        )}

        <ScrollArea className="h-64 rounded-md border p-2">
          {clusters.length === 0 ? (
            <div className="text-muted-foreground flex h-full items-center justify-center text-sm">
              No face collections found.
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-3">
              {clusters.map((cluster) => {
                const isSelected = selectedIds.has(cluster.cluster_id);
                return (
                  <button
                    key={cluster.cluster_id}
                    type="button"
                    onClick={() =>
                      setSelectedIds((prev) => {
                        const next = new Set(prev);
                        isSelected
                          ? next.delete(cluster.cluster_id)
                          : next.add(cluster.cluster_id);
                        return next;
                      })
                    }
                    className={cn(
                      'flex flex-col items-center gap-1.5 rounded-lg border-2 p-2 transition-colors',
                      'hover:bg-accent focus-visible:ring-ring focus-visible:ring-2 focus-visible:outline-none',
                      isSelected
                        ? 'border-primary bg-primary/10'
                        : 'bg-muted/40 border-transparent',
                    )}
                  >
                    <div className="relative">
                      <PersonAvatar
                        cluster={cluster}
                        className="border-accent-foreground h-14 w-14 border-[1px]"
                      />
                      {isSelected && (
                        <span className="bg-primary text-primary-foreground absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold">
                          ✓
                        </span>
                      )}
                    </div>
                    <span className="w-full truncate text-center text-xs font-medium">
                      {getPersonName(cluster)}
                    </span>
                    <span className="text-muted-foreground text-[10px]">
                      {getPhotoCountText(cluster.face_count)}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </ScrollArea>

        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={() => setSelectedIds(new Set())}
            disabled={selectedIds.size === 0}
          >
            Clear
          </Button>
          <Button
            disabled={selectedIds.size === 0}
            onClick={() => {
              dispatch(showLoader('Searching...'));
              mutate({
                cluster_ids: [...selectedIds],
                match_mode: matchMode,
              });
            }}
          >
            Search{selectedIds.size > 0 ? ` (${selectedIds.size})` : ''}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
