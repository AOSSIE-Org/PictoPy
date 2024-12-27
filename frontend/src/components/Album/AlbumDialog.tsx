import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '../ui/textarea';
import { EditAlbumDialogProps } from '@/types/Album';
import { queryClient, usePictoMutation } from '@/hooks/useQueryExtensio';
import { editAlbumDescription } from '../../../api/api-functions/albums';

const EditAlbumDialog: React.FC<EditAlbumDialogProps> = ({
  album,
  onClose,
  onSuccess,
  onError,
}) => {
  const { mutate: editDescription, isPending: isEditing } = usePictoMutation({
    mutationFn: editAlbumDescription,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['view-album', album?.album_name],
      });
    },
    autoInvalidateTags: ['all-albums'],
  });
  const [description, setDescription] = useState(album?.description || '');

  useEffect(() => {
    setDescription(album?.description || '');
  }, [album]);

  const handleEditAlbum = async () => {
    if (album) {
      try {
        await editDescription({ album_name: album?.album_name, description });
        onSuccess();
      } catch (err) {
        onError('Error Editing Album', err);
      }
    }
  };

  return (
    <Dialog open={!!album} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Album: {album?.album_name}</DialogTitle>
        </DialogHeader>
        <Textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Album description"
          className="my-4"
        />
        <DialogFooter>
          <Button onClick={handleEditAlbum} disabled={isEditing}>
            {isEditing ? 'Saving...' : 'Save'}
          </Button>
          <Button onClick={onClose} variant="outline">
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default EditAlbumDialog;
