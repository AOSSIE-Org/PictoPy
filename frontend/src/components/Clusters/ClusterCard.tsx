import React, { memo, useState } from 'react';
import { useNavigate } from 'react-router';
import { Pencil, Trash2, Images, Check, X } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ManualCluster } from '@/types/ManualCluster';

interface ClusterCardProps {
  cluster: ManualCluster;
  onRename: (clusterId: string, newName: string) => Promise<boolean>;
  onDelete: (clusterId: string) => Promise<boolean>;
}

export const ClusterCard = memo(function ClusterCard({
  cluster,
  onRename,
  onDelete,
}: ClusterCardProps) {
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [nameInput, setNameInput] = useState(cluster.name);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = nameInput.trim();
    if (!trimmed || trimmed === cluster.name) {
      setEditing(false);
      setNameInput(cluster.name);
      return;
    }
    setSaving(true);
    const ok = await onRename(cluster.cluster_id, trimmed);
    setSaving(false);
    if (ok) setEditing(false);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Delete cluster "${cluster.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    await onDelete(cluster.cluster_id);
    setDeleting(false);
  };

  const handleCardClick = () => {
    if (!editing) navigate(`/clusters/${cluster.cluster_id}`);
  };

  return (
    <Card
      className="border-primary/20 hover:border-primary/60 cursor-pointer transition-colors"
      onClick={handleCardClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          {editing ? (
            <form
              onSubmit={handleRenameSubmit}
              className="flex flex-1 items-center gap-1"
              onClick={(e) => e.stopPropagation()}
            >
              <Input
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                autoFocus
                disabled={saving}
                className="h-7 text-sm"
                maxLength={80}
              />
              <Button
                type="submit"
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                disabled={saving}
              >
                <Check className="h-3.5 w-3.5" />
              </Button>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={() => {
                  setEditing(false);
                  setNameInput(cluster.name);
                }}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </form>
          ) : (
            <span className="line-clamp-2 flex-1 font-semibold">
              {cluster.name}
            </span>
          )}

          {!editing && (
            <div className="flex shrink-0 gap-1">
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                title="Rename"
                onClick={(e) => {
                  e.stopPropagation();
                  setEditing(true);
                }}
              >
                <Pencil className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="text-destructive hover:text-destructive h-7 w-7"
                title="Delete"
                disabled={deleting}
                onClick={handleDelete}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </div>

        <div className="text-muted-foreground mt-3 flex items-center gap-1 text-xs">
          <Images className="h-3.5 w-3.5" />
          <span>
            {cluster.image_count}{' '}
            {cluster.image_count === 1 ? 'image' : 'images'}
          </span>
        </div>
      </CardContent>
    </Card>
  );
});
