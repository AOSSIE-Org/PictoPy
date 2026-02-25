/**
 * ImagePickerModal
 *
 * A modal gallery picker that lets the user multi-select images from their
 * library and then bulk-assign them to the current cluster.
 *
 * Performance notes:
 * - Images are paginated (PAGE_SIZE per load)
 * - Cards are memoized via React.memo
 * - Selection state uses a Set and local state only – no Redux involved
 */

import React, {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CheckCircle2, Circle, Loader2, Search } from 'lucide-react';
import { Image } from '@/types/Media';

const PAGE_SIZE = 40;

interface ImagePickerModalProps {
  open: boolean;
  onClose: () => void;
  allImages: Image[];
  /** image ids already in the cluster – grey them out */
  assignedIds: Set<string>;
  onAssign: (selectedIds: string[]) => Promise<void>;
  assigning: boolean;
}

export function ImagePickerModal({
  open,
  onClose,
  allImages,
  assignedIds,
  onAssign,
  assigning,
}: ImagePickerModalProps) {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(search), 300);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [search]);

  // Reset on open
  useEffect(() => {
    if (open) {
      setSelected(new Set());
      setSearch('');
      setDebouncedSearch('');
      setPage(1);
    }
  }, [open]);

  const filtered = useMemo(() => {
    const q = debouncedSearch.toLowerCase();
    if (!q) return allImages;
    return allImages.filter(
      (img) =>
        img.path.toLowerCase().includes(q) ||
        img.metadata?.name?.toString().toLowerCase().includes(q),
    );
  }, [allImages, debouncedSearch]);

  const paged = useMemo(
    () => filtered.slice(0, page * PAGE_SIZE),
    [filtered, page],
  );

  const loadMore = useCallback(
    () => setPage((p) => p + 1),
    [],
  );

  const toggle = useCallback(
    (id: string) => {
      setSelected((prev) => {
        const next = new Set(prev);
        next.has(id) ? next.delete(id) : next.add(id);
        return next;
      });
    },
    [],
  );

  const selectAll = useCallback(() => {
    setSelected(new Set(filtered.map((i) => i.id)));
  }, [filtered]);

  const clearAll = useCallback(() => setSelected(new Set()), []);

  const handleAssign = async () => {
    if (selected.size === 0) return;
    await onAssign(Array.from(selected));
  };

  const hasMore = paged.length < filtered.length;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-hidden p-0">
        <DialogHeader className="px-6 pt-6">
          <DialogTitle>Add Images to Cluster</DialogTitle>
        </DialogHeader>

        {/* Toolbar */}
        <div className="flex items-center gap-2 border-b px-6 pb-4">
          <div className="relative flex-1">
            <Search className="text-muted-foreground absolute top-2.5 left-2.5 h-4 w-4" />
            <Input
              className="pl-8"
              placeholder="Search by filename…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button size="sm" variant="outline" onClick={selectAll}>
            Select all ({filtered.length})
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={clearAll}
            disabled={selected.size === 0}
          >
            Clear
          </Button>
        </div>

        {/* Grid */}
        <div className="hide-scrollbar overflow-y-auto px-6 py-4" style={{ maxHeight: '55vh' }}>
          {paged.length === 0 ? (
            <p className="text-muted-foreground text-center text-sm py-12">
              No images found.
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6">
              {paged.map((img) => (
                <PickerImageCard
                  key={img.id}
                  image={img}
                  selected={selected.has(img.id)}
                  alreadyAssigned={assignedIds.has(img.id)}
                  onToggle={toggle}
                />
              ))}
            </div>
          )}

          {hasMore && (
            <div className="mt-4 flex justify-center">
              <Button variant="outline" size="sm" onClick={loadMore}>
                Load more ({filtered.length - paged.length} remaining)
              </Button>
            </div>
          )}
        </div>

        <DialogFooter className="border-t px-6 py-4">
          <span className="text-muted-foreground mr-auto text-sm">
            {selected.size} image{selected.size !== 1 ? 's' : ''} selected
          </span>
          <Button variant="outline" onClick={onClose} disabled={assigning}>
            Cancel
          </Button>
          <Button
            onClick={handleAssign}
            disabled={selected.size === 0 || assigning}
          >
            {assigning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Assigning…
              </>
            ) : (
              `Assign ${selected.size > 0 ? `(${selected.size})` : ''}`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Memoized picker card
// ---------------------------------------------------------------------------

interface PickerImageCardProps {
  image: Image;
  selected: boolean;
  alreadyAssigned: boolean;
  onToggle: (id: string) => void;
}

const PickerImageCard = memo(function PickerImageCard({
  image,
  selected,
  alreadyAssigned,
  onToggle,
}: PickerImageCardProps) {
  const src = image.thumbnailPath || image.path;

  return (
    <div
      className={`relative cursor-pointer overflow-hidden rounded-md border-2 transition-all ${
        selected
          ? 'border-primary'
          : alreadyAssigned
            ? 'border-muted opacity-50'
            : 'border-transparent hover:border-primary/50'
      }`}
      style={{ aspectRatio: '1/1' }}
      onClick={() => !alreadyAssigned && onToggle(image.id)}
      title={alreadyAssigned ? 'Already in this cluster' : ''}
    >
      <img
        src={src}
        alt={image.metadata?.name?.toString() ?? image.id}
        className="h-full w-full object-cover"
        loading="lazy"
      />
      <div className="absolute top-1 right-1">
        {selected ? (
          <CheckCircle2 className="text-primary drop-shadow h-5 w-5" />
        ) : (
          !alreadyAssigned && (
            <Circle className="text-white/70 drop-shadow h-5 w-5" />
          )
        )}
      </div>
    </div>
  );
});
