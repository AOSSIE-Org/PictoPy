import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '../ui/textarea';
import { CreateAlbumFormProps } from '@/types/Album';
import { usePictoMutation } from '@/hooks/useQueryExtensio';
import { createAlbums } from '../../../api/api-functions/albums';

const CreateAlbumForm: React.FC<CreateAlbumFormProps> = ({
  isOpen,
  onClose,
  onSuccess,
  onError,
}) => {
  const [newAlbumName, setNewAlbumName] = useState('');
  const [newAlbumDescription, setNewAlbumDescription] = useState('');
  const { mutate: createAlbum, isPending: isCreating } = usePictoMutation({
    mutationFn: createAlbums,
    autoInvalidateTags: ['all-albums'],
  });

  const handleCreateAlbum = async () => {
    if (newAlbumName.trim()) {
      try {
        await createAlbum({
          name: newAlbumName.trim(),
          description: newAlbumDescription.trim(),
        });
        setNewAlbumName('');
        setNewAlbumDescription('');
        onSuccess();
        onClose();
      } catch (err) {
        onError('Error Creating Album', err);
      }
    } else {
      onError('Invalid Album Name', new Error('Album name cannot be empty'));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Album</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Input
            type="text"
            value={newAlbumName}
            onChange={(e) => setNewAlbumName(e.target.value)}
            placeholder="New album name"
            required
          />
          <Textarea
            value={newAlbumDescription}
            onChange={(e) => setNewAlbumDescription(e.target.value)}
            placeholder="Album description (optional)"
          />
        </div>
        <DialogFooter>
          <Button
            onClick={handleCreateAlbum}
            disabled={isCreating || !newAlbumName.trim()}
          >
            {isCreating ? 'Creating...' : 'Create Album'}
          </Button>
          <Button onClick={onClose} variant="outline">
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CreateAlbumForm;
