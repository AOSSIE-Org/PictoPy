import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Alert } from '@/components/ui/alert';
import { X } from 'lucide-react';
import { getAvailableClasses } from '@/api/api-functions/smart_albums';

interface CreateAlbumDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (name: string, classes: string[], autoUpdate: boolean) => Promise<void>;
}

export const CreateAlbumDialog: React.FC<CreateAlbumDialogProps> = ({
  open,
  onClose,
  onCreate,
}) => {
  const [albumName, setAlbumName] = useState('');
  const [selectedClasses, setSelectedClasses] = useState<string[]>([]);
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [availableClasses, setAvailableClasses] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const classes = await getAvailableClasses();
        setAvailableClasses(classes);
      } catch (err) {
        console.error('Failed to fetch classes:', err);
      }
    };

    if (open) {
      fetchClasses();
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!albumName.trim()) {
      setError('Album name is required');
      return;
    }

    if (selectedClasses.length === 0) {
      setError('Please select at least one object class');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onCreate(albumName, selectedClasses, autoUpdate);
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create album');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setAlbumName('');
    setSelectedClasses([]);
    setAutoUpdate(true);
    setError(null);
    setSearchTerm('');
    onClose();
  };

  const toggleClass = (className: string) => {
    setSelectedClasses((prev) =>
      prev.includes(className) ? prev.filter((c) => c !== className) : [...prev, className]
    );
  };

  const filteredClasses = availableClasses.filter((c) =>
    c.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Smart Album</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Album Name */}
          <div className="space-y-2">
            <Label htmlFor="album-name">Album Name</Label>
            <Input
              id="album-name"
              value={albumName}
              onChange={(e) => setAlbumName(e.target.value)}
              placeholder="e.g., My Pets, Vacation Photos"
              autoFocus
            />
          </div>

          {/* Object Classes */}
          <div className="space-y-2">
            <Label>Object Classes ({selectedClasses.length} selected)</Label>
            <Input
              placeholder="Search classes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            {/* Selected Classes */}
            {selectedClasses.length > 0 && (
              <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg">
                {selectedClasses.map((className) => (
                  <Badge key={className} variant="default" className="gap-1">
                    {className}
                    <button onClick={() => toggleClass(className)}>
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}

            {/* Available Classes */}
            <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto p-3 border rounded-lg">
              {filteredClasses.map((className) => (
                <Badge
                  key={className}
                  variant={selectedClasses.includes(className) ? 'default' : 'outline'}
                  className="cursor-pointer justify-center"
                  onClick={() => toggleClass(className)}
                >
                  {className}
                </Badge>
              ))}
            </div>
          </div>

          {/* Quick Select */}
          <div className="space-y-2">
            <Label>Quick Select:</Label>
            <div className="flex gap-2 flex-wrap">
              <Badge
                variant="outline"
                className="cursor-pointer"
                onClick={() => setSelectedClasses(['dog', 'cat', 'bird'])}
              >
                Pets
              </Badge>
              <Badge
                variant="outline"
                className="cursor-pointer"
                onClick={() => setSelectedClasses(['car', 'truck', 'bus'])}
              >
                Vehicles
              </Badge>
              <Badge
                variant="outline"
                className="cursor-pointer"
                onClick={() => setSelectedClasses(['person'])}
              >
                People
              </Badge>
            </div>
          </div>

          {/* Auto Update */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="space-y-1">
              <Label>Auto-Update Album</Label>
              <p className="text-sm text-gray-600">Automatically add new matching images</p>
            </div>
            <Switch checked={autoUpdate} onCheckedChange={setAutoUpdate} />
          </div>

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <p>{error}</p>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading || !albumName.trim() || selectedClasses.length === 0}
          >
            {loading ? 'Creating...' : 'Create Album'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};