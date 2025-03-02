import { FC } from 'react';
import { Button } from '@/components/ui/button';

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
interface DeleteImagesDialogProps {
    isOpen : boolean;
    setIsOpen : (e:boolean) => void;
    executeDeleteImages : (e:boolean) => void;
}


const DeleteImagesDialog:FC<DeleteImagesDialogProps> = ({ 
    isOpen,
    setIsOpen,
    executeDeleteImages
}) => {

  const handleDeleteImages = (status : boolean) => {
    executeDeleteImages(status);
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Do you also want to delete these images from Device ?</DialogTitle>
        </DialogHeader>

        <DialogFooter>
          <Button onClick={()=>handleDeleteImages(true)}>
            {/* {isEditing ? 'Saving...' : 'Yes'} */}
            Yes
          </Button>
          <Button variant="outline" onClick={()=>handleDeleteImages(false)} >
            No
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DeleteImagesDialog;
