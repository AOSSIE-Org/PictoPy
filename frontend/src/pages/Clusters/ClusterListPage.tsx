import React, { useEffect, useState } from 'react';
import { Plus, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ClusterCard } from '@/components/Clusters/ClusterCard';
import { useManualClusters } from '@/hooks/useManualClusters';

export function ClusterListPage() {
  const {
    clusters,
    loading,
    error,
    clearError,
    loadClusters,
    createCluster,
    renameCluster,
    deleteCluster,
  } = useManualClusters();

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadClusters();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    const result = await createCluster(name);
    setCreating(false);
    if (result) {
      setShowCreate(false);
      setNewName('');
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Clusters</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Create and manage custom image groupings, independent from AI
            face-detection clusters.
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Cluster
        </Button>
      </div>

      {/* Error banner */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            {error}
            <Button
              size="sm"
              variant="ghost"
              className="ml-4 h-6"
              onClick={clearError}
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Content */}
      {loading && clusters.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="text-muted-foreground h-8 w-8 animate-spin" />
        </div>
      ) : clusters.length === 0 ? (
        <div className="text-muted-foreground flex flex-1 flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-12">
          <p className="text-lg font-medium">No clusters yet</p>
          <p className="text-sm">
            Click "Create Cluster" to start organising your images manually.
          </p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => setShowCreate(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Create your first cluster
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {clusters.map((cluster) => (
            <ClusterCard
              key={cluster.cluster_id}
              cluster={cluster}
              onRename={renameCluster}
              onDelete={deleteCluster}
            />
          ))}
        </div>
      )}

      {/* Create dialog */}
      <Dialog
        open={showCreate}
        onOpenChange={(v) => {
          if (!v) {
            setShowCreate(false);
            setNewName('');
          }
        }}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Create New Cluster</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="flex flex-col gap-4">
            <Input
              placeholder="Cluster name…"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
              maxLength={80}
              disabled={creating}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreate(false);
                  setNewName('');
                }}
                disabled={creating}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!newName.trim() || creating}
              >
                {creating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating…
                  </>
                ) : (
                  'Create'
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
