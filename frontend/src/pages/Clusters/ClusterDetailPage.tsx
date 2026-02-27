import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import {
  ArrowLeft,
  AlertCircle,
  Loader2,
  Plus,
  Trash2,
  Pencil,
  Check,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ImagePickerModal } from '@/components/Clusters/ImagePickerModal';
import { useManualClusters } from '@/hooks/useManualClusters';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import { Image } from '@/types/Media';
import { ManualClusterImage } from '@/types/ManualCluster';

export function ClusterDetailPage() {
  const { clusterId } = useParams<{ clusterId: string }>();
  const navigate = useNavigate();

  const {
    details,
    loading,
    error,
    clearError,
    loadClusterDetail,
    renameCluster,
    deleteCluster,
    assignImages,
    removeImageFromClusters,
  } = useManualClusters();

  const detail = clusterId ? details[clusterId] : undefined;

  // Load cluster detail on mount
  useEffect(() => {
    if (clusterId) loadClusterDetail(clusterId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clusterId]);

  // Load all images for the picker (only once)
  const { data: allImagesData } = usePictoQuery({
    queryKey: ['all-images-for-picker'],
    queryFn: () => fetchAllImages(),
  });
  const allImages: Image[] = useMemo(
    () => (allImagesData?.data as Image[]) ?? [],
    [allImagesData],
  );

  // Inline rename state
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [savingName, setSavingName] = useState(false);

  const startEdit = () => {
    setNameInput(detail?.cluster.name ?? '');
    setEditingName(true);
  };

  const submitRename = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = nameInput.trim();
    if (!trimmed || !clusterId) {
      setEditingName(false);
      return;
    }
    setSavingName(true);
    await renameCluster(clusterId, trimmed);
    setSavingName(false);
    setEditingName(false);
  };

  // Delete cluster
  const handleDelete = async () => {
    if (!clusterId) return;
    if (!window.confirm(`Delete this cluster? This cannot be undone.`)) return;
    const ok = await deleteCluster(clusterId);
    if (ok) navigate('/clusters');
  };

  // Image picker modal
  const [pickerOpen, setPickerOpen] = useState(false);
  const [assigning, setAssigning] = useState(false);

  const assignedIds = useMemo(
    () => new Set((detail?.images ?? []).map((i: ManualClusterImage) => i.id)),
    [detail],
  );

  const handleAssign = useCallback(
    async (selectedIds: string[]) => {
      if (!clusterId) return;
      setAssigning(true);
      await assignImages(clusterId, selectedIds);
      setAssigning(false);
      setPickerOpen(false);
    },
    [assignImages, clusterId],
  );

  const handleRemove = useCallback(
    async (imageId: string) => {
      if (!clusterId) return;
      await removeImageFromClusters(clusterId, imageId);
    },
    [removeImageFromClusters, clusterId],
  );

  // ── Render ───────────────────────────────────────────────────────────────

  if (!detail && loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="text-muted-foreground h-10 w-10 animate-spin" />
      </div>
    );
  }

  if (!detail && !loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground text-lg">Cluster not found.</p>
        <Button variant="outline" onClick={() => navigate('/clusters')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Clusters
        </Button>
      </div>
    );
  }

  const { cluster, images } = detail!;

  return (
    <div className="flex h-full flex-col">
      {/* Top bar */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/clusters')}
          className="mr-1"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          Clusters
        </Button>

        {/* Cluster name (editable) */}
        {editingName ? (
          <form
            onSubmit={submitRename}
            className="flex items-center gap-1"
          >
            <Input
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              autoFocus
              disabled={savingName}
              className="h-9 text-xl font-bold"
              maxLength={80}
            />
            <Button type="submit" size="icon" variant="ghost" disabled={savingName}>
              <Check className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              size="icon"
              variant="ghost"
              onClick={() => setEditingName(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </form>
        ) : (
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            {cluster.name}
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              title="Rename cluster"
              onClick={startEdit}
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          </h1>
        )}

        <div className="ml-auto flex items-center gap-2">
          <span className="text-muted-foreground text-sm">
            {cluster.image_count} image{cluster.image_count !== 1 ? 's' : ''}
          </span>
          <Button size="sm" onClick={() => setPickerOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Images
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={handleDelete}
            disabled={loading}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete Cluster
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            {error}
            <Button size="sm" variant="ghost" className="ml-4 h-6" onClick={clearError}>
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Image grid */}
      {images.length === 0 ? (
        <div className="text-muted-foreground flex flex-1 flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-12">
          <p className="text-lg font-medium">No images in this cluster</p>
          <p className="text-sm">
            Click "Add Images" to assign images to this cluster.
          </p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => setPickerOpen(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Images
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {images.map((img: ManualClusterImage) => (
            <ClusterImageCard
              key={img.id}
              image={img}
              onRemove={handleRemove}
            />
          ))}
        </div>
      )}

      {/* Image picker modal */}
      <ImagePickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        allImages={allImages}
        assignedIds={assignedIds}
        onAssign={handleAssign}
        assigning={assigning}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small sub-component: single image in the detail grid
// ---------------------------------------------------------------------------

interface ClusterImageCardProps {
  image: ManualClusterImage;
  onRemove: (imageId: string) => void;
}

function ClusterImageCard({ image, onRemove }: ClusterImageCardProps) {
  const [removing, setRemoving] = useState(false);
  const src = image.thumbnailPath || image.path;

  const handleRemove = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Remove this image from the cluster?')) return;
    setRemoving(true);
    await onRemove(image.id);
    setRemoving(false);
  };

  return (
    <div
      className="group relative overflow-hidden rounded-md border"
      style={{ aspectRatio: '1/1' }}
    >
      <img
        src={src}
        alt={image.id}
        className="h-full w-full object-cover"
        loading="lazy"
      />
      <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100">
        <Button
          size="icon"
          variant="destructive"
          className="h-8 w-8"
          disabled={removing}
          onClick={handleRemove}
          title="Remove from cluster"
        >
          {removing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
